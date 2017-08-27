using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using CustomElements;

namespace KeywordSearchInterface {
    
    /// <summary>
    /// Searches an index file and displays results
    /// </summary>
    public class ImageProvider : ISearchProvider {

        private string IndexFilePath = ".\\files.index";
        private string ImageFolderPath = ".\\images\\";

        /// <summary>
        /// Called with default values of <see cref="IndexFilePath"/> and <see cref="ImageFolderPath"/>.
        /// </summary>
        /// <param name="lp">For class name to class id conversion</param>
        public ImageProvider(LabelProvider lp) {
            LabelProvider = lp;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        /// <param name="lp">For class name to class id conversion</param>
        /// <param name="filePath">Relative or absolute path to index file</param>
        /// <param name="folderPath">Relative or absolute path to image folder</param>
        public ImageProvider(LabelProvider lp, string filePath, string folderPath) {
            LabelProvider = lp;

            IndexFilePath = filePath;
            ImageFolderPath = folderPath;

            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private LabelProvider LabelProvider;
        private Dictionary<int, List<Filename>> Classes = new Dictionary<int, List<Filename>>();
        private Task LoadTask { get; set; }
        private CancellationTokenSource CTS;

        #region (Private) Index File Loading

        private void LoadFromFile() {
            BufferedByteStream stream = null;
            Dictionary<int, int> classLocations = new Dictionary<int, int>();

            try {
                stream = new BufferedByteStream(IndexFilePath);

                // header = 'KS INDEX'+(Int64)-1
                if (stream.ReadInt64() != 0x4b5320494e444558 && stream.ReadInt64() != -1)
                    throw new FileFormatException("Invalid index file format.");
                
                // read offests of each class
                while (true) {
                    int value = stream.ReadInt32();
                    int valueOffset = stream.ReadInt32();

                    if (value != -1) {
                        classLocations.Add(valueOffset, value);
                    } else break;
                }

                while (true) {
                    if (stream.IsEndOfStream()) break;

                    // list of class offets does not contain this one
                    if (!classLocations.ContainsKey(stream.Pointer))
                        throw new FileFormatException("Invalid index file format.");

                    int classId = classLocations[stream.Pointer];
                    Classes.Add(classId, new List<Filename>());

                    // add all images
                    while (true) {
                        uint imageId = (uint)stream.ReadInt32();
                        float imageProbability = stream.ReadFloat();

                        if (imageId != 0xffffffff) {
                            Classes[classId].Add(new Filename() { Id = imageId, Probability = imageProbability });
                        } else break;
                    }
                }
            } finally {
                stream.Dispose();
            }
        }

        #endregion

        #region Interface Methods

        /// <summary>
        /// Searches the index file asynchronously and calls <see cref="SearchResultsReadyEvent"/>.
        /// </summary>
        /// <param name="filter">A string the resuts should be for</param>
        public void Search(string filter) {
            if (LabelProvider.LoadTask.IsFaulted) {
                ShowSearchMessageEvent(SearchMessageType.Exception, LabelProvider.LoadTask.Exception.InnerException.Message);
                return;
            } else if (LoadTask.IsFaulted) {
                ShowSearchMessageEvent(SearchMessageType.Exception, LoadTask.Exception.InnerException.Message);
                return;
            } else if (!LabelProvider.LoadTask.IsCompleted || !LoadTask.IsCompleted) {
                ShowSearchMessageEvent(SearchMessageType.ResourcesNotLoadedYet, filter);
                return;
            }

            // parse the search phrase
            List<List<int>> ids = GetClassIds(filter);
            if (ids == null) return;

            CTS = new CancellationTokenSource();

            Task.Factory.StartNew(() => {
                return GetFilenames(ids, CTS.Token);
            }, CTS.Token, TaskCreationOptions.None, TaskScheduler.Default).ContinueWith((Task<List<Filename>> task) => {
                if (task.IsFaulted) {
                    ShowSearchMessageEvent(SearchMessageType.Exception, task.Exception.InnerException.Message);
                    return;
                }
                if (task.Result == null) return;

                SearchResultsReadyEvent(task.Result);
            }, CTS.Token, TaskContinuationOptions.NotOnCanceled, TaskScheduler.Default);
        }

        /// <summary>
        /// Calls Cancel() on <see cref="CancellationTokenSource">CancellationTokenSource</see> resulting in cancelation of a search task.
        /// </summary>
        public void CancelSearch() {
            CTS?.Cancel();
        }

        #endregion

        #region Events

        /// <summary>
        /// Delegate for <see cref="SearchResultsReadyEvent"/>
        /// </summary>
        public delegate void SearchResultsReady(List<Filename> filenames);

        /// <summary>
        /// Called when new result are ready and should be shown
        /// </summary>
        public event SearchResultsReady SearchResultsReadyEvent;

        /// <summary>
        /// Delegate for <see cref="ShowSearchMessageEvent"/>
        /// </summary>
        /// <param name="type">Type of an message</param>
        /// <param name="message">A text the message to show</param>
        public delegate void ShowSearchMessage(SearchMessageType type, string message);

        /// <summary>
        /// Called when an UI message should be shown
        /// </summary>
        public event ShowSearchMessage ShowSearchMessageEvent;

        #endregion

        #region (Private) List Unions & Multiplications

        private struct ListOrDictionary {
            public List<Filename> List;
            public Dictionary<uint, Filename> Dictionary;
        }

        /// <summary>
        /// Creates list of results for a display.
        /// </summary>
        /// <param name="ids">Parsed list of ids</param>
        /// <param name="token"></param>
        /// <returns>List of <see cref="Filename"/>s</returns>
        private List<Filename> GetFilenames(List<List<int>> ids, CancellationToken token) {
            List<ListOrDictionary> afterUnion = DoListUnions(ids, token);
            if (afterUnion == null) return null;
            return DoListMultiplications(afterUnion, token);
        }

        /// <summary>
        /// Does set multiplication - returns elements present in all sets with probabilities from each set multiplied.
        /// </summary>
        /// <param name="lists">List of classes where each class is represented by a list or a dictionary of its images</param>
        /// <param name="token"></param>
        /// <returns>Elements present in all sets with probabilities from each set multiplied</returns>
        private List<Filename> DoListMultiplications(List<ListOrDictionary> lists, CancellationToken token) {
            if (lists.Count == 1 && lists[0].List != null)
                return lists[0].List;

            // find a dictionary (since classes can be represented also as lists)
            Dictionary<uint, Filename> dict = null;
            for (int i = 0; i < lists.Count; i++) {
                if (lists[i].Dictionary != null) {
                    dict = lists[i].Dictionary;
                    lists.RemoveAt(i);
                    break;
                }
            }
            // if no dictionary, make one
            if (dict == null) {
                dict = lists[lists.Count - 1].List.ToDictionary(f => f.Id);
                lists.RemoveAt(lists.Count - 1);
            }

            // iterate over each list and check if element in dictionary and behave accordingly
            Filename fIn;
            foreach (ListOrDictionary item in lists) {
                Dictionary<uint, Filename> tempDict = new Dictionary<uint, Filename>();

                if (item.List != null) {
                    foreach (Filename f in item.List) {
                        if (token.IsCancellationRequested) return null;

                        if (dict.TryGetValue(f.Id, out fIn)) {
                            fIn.Probability = fIn.Probability * f.Probability;
                            tempDict.Add(f.Id, fIn);
                        }
                    }
                } else {
                    foreach (KeyValuePair<uint, Filename> f in item.Dictionary) {
                        if (token.IsCancellationRequested) return null;

                        if (dict.TryGetValue(f.Value.Id, out fIn)) {
                            fIn.Probability = fIn.Probability * f.Value.Probability;
                            tempDict.Add(f.Value.Id, fIn);
                        }
                    }
                }
                dict = tempDict;
            }

            var list = new List<Filename>();
            list.Capacity = dict.Count;

            if (token.IsCancellationRequested) return null;

            foreach (var item in dict) {
                list.Add(item.Value);
            }

            if (!token.IsCancellationRequested)
                list.Sort();
            return list;
        }

        /// <summary>
        /// Merge files from classes in each list of ids.
        /// </summary>
        /// <param name="ids">Lists to be merged</param>
        /// <param name="token"></param>
        /// <returns></returns>
        private List<ListOrDictionary> DoListUnions(List<List<int>> ids, CancellationToken token) {
            var list = new List<ListOrDictionary>();

            // should be fast
            // http://alicebobandmallory.com/articles/2012/10/18/merge-collections-without-duplicates-in-c
            Filename fIn;
            foreach (List<int> listOfIds in ids) {
                if (listOfIds.Count == 1) {
                    list.Add(new ListOrDictionary() { List = Classes[listOfIds[0]] });
                    continue;
                }
                Dictionary<uint, Filename> dict = Classes[listOfIds[0]].ToDictionary(f => f.Id);
                for (int i = 1; i < listOfIds.Count; i++) {
                    foreach (Filename f in Classes[listOfIds[i]]) {
                        if (token.IsCancellationRequested) return null;

                        if (dict.TryGetValue(f.Id, out fIn)) {
                            fIn.Probability += f.Probability;
                            dict[f.Id] = fIn;
                        } else {
                            dict.Add(f.Id, f);
                        }
                    }
                }
                list.Add(new ListOrDictionary() { Dictionary = dict });
            }
            return list;
        }

        #endregion

        #region (Private) Parse Search Term

        /// <summary>
        /// Parses string of classes (eg. tree+castle*car -> {{tree, castle}, {car}})
        /// </summary>
        private List<List<int>> GetClassIds(string filter) {
            var parts = filter.Split('*');

            Label label = null;
            List<List<int>> list = new List<List<int>>();

            for (int p = 0; p < parts.Length; p++) {
                var classes = parts[p].Split('+');

                list.Add(new List<int>());

                for (int i = 0; i < classes.Length; i++) {
                    string cls = classes[i].Trim();

                    if (cls == string.Empty) {
                        ShowSearchMessageEvent(SearchMessageType.InvalidFormat, filter);
                        return null;
                    }

                    if (!LabelProvider.Labels.TryGetValue(cls, out label)) {
                        ShowSearchMessageEvent(SearchMessageType.InvalidLabel, cls);
                        return null;
                    }
                    if (!Classes.ContainsKey(label.Id)) continue;

                    list[p].Add(label.Id);
                }
            }
            for (int p = 0; p < list.Count; p++) {
                if (list[p].Count == 0) {
                    ShowSearchMessageEvent(SearchMessageType.NotFound, parts[p]);
                    return null;
                }
            }
            return list;
        }

        #endregion

    }

    /// <summary>
    /// Type of message to be shown instead of the results
    /// </summary>
    public enum SearchMessageType { Exception, NotFound, InvalidLabel, InvalidFormat, ResourcesNotLoadedYet }

}
