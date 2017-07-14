using CustomElements;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;

namespace KeywordSearch {

    struct Thumbnail {
        public Filename Filename { get; set; }
        public BitmapImage Image { get; set; }
    }

    struct Filename : IComparable<Filename> {
        public uint Id { get; set; }
        public float Probability { get; set; }

        public int CompareTo(Filename other) {
            return -Probability.CompareTo(other.Probability);
        }
    }

    class ImageProvider : ISearchProvider {

        private string IndexFilePath = ".\\files.index";
        private string ImageFolderPath = ".\\images\\";

        public ImageProvider(LabelProvider lp) {
            LabelProvider = lp;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        public ImageProvider(LabelProvider lp, string filePath, string folderPath) {
            LabelProvider = lp;

            IndexFilePath = filePath;
            ImageFolderPath = folderPath;

            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private LabelProvider LabelProvider;
        private Dictionary<int, List<Filename>> Classes = new Dictionary<int, List<Filename>>();
        private Task LoadTask { get; set; }
        public ItemsControl ItemsControl { get; set; }
        public ContentControl NotFoundMessageBox { get; set; }

        private void LoadFromFile() {
            BufferedByteStream stream = null;
            Dictionary<int, int> classLocations = new Dictionary<int, int>();

            try {
                stream = new BufferedByteStream(IndexFilePath);

                if (stream.ReadInt64() != 0x4b5320494e444558 && stream.ReadInt64() != -1)
                    throw new FileFormatException("Invalid index file format.");
                
                while (true) {
                    int value = stream.ReadInt32();
                    int valueOffset = stream.ReadInt32();

                    if (value != -1) {
                        classLocations.Add(valueOffset, value);
                    } else break;
                }

                while (true) {
                    if (stream.IsEndOfStream()) break;

                    if (!classLocations.ContainsKey(stream.Pointer))
                        throw new FileFormatException("Invalid index file format.");

                    int classId = classLocations[stream.Pointer];
                    Classes.Add(classId, new List<Filename>());

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

        private BitmapImage GetImage(uint id) {
            BitmapImage bmp = new BitmapImage();

            bmp.BeginInit();
            bmp.UriSource = new Uri(string.Format("{0}{1}.jpg", ImageFolderPath, id), UriKind.Relative);
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.EndInit();
            bmp.Freeze();

            return bmp;
        }

        CancellationTokenSource CTS;

        public void Search(string filter, SuggestionTextBox suggestionTextBox) {
            if (LabelProvider.LoadTask.IsFaulted) {
                suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                    () => { MessageBox.Show(LabelProvider.LoadTask.Exception.InnerException.Message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                    ));
                return;
            } else if (LoadTask.IsFaulted) {
                suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                    () => { MessageBox.Show(LoadTask.Exception.InnerException.Message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                    ));
                return;
            } else if (!LabelProvider.LoadTask.IsCompleted || !LoadTask.IsCompleted) {
                ShowNotFoundMessageBox(NotFoundMessageType.ResourcesNotLoadedYet, filter);
                return;
            }

            if (ItemsControl == null) {
                suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                    () => { MessageBox.Show("ImageProvider has no reference to ItemsControl.", "Error", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                    ));
                return;
            }

            List<List<int>> ids = GetClassIds(filter);
            if (ids == null) return;

            CTS = new CancellationTokenSource();

            Task.Factory.StartNew(() => {
                return GetThumbnails(ids, CTS.Token);
            }, CTS.Token, TaskCreationOptions.None, TaskScheduler.Default).ContinueWith((Task<List<Thumbnail>> task) => {
                if (task.IsFaulted) {
                    suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                        () => { MessageBox.Show(task.Exception.InnerException.Message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                        ));
                    return;
                }
                if (task.Result == null) return;

                suggestionTextBox.Dispatcher.BeginInvoke(
                    new Action<List<Thumbnail>>(UpdateThumbnails),
                    new object[] { task.Result }
                    );
            }, CTS.Token, TaskContinuationOptions.NotOnCanceled, TaskScheduler.Default);
        }

        private List<Thumbnail> GetThumbnails(List<List<int>> ids, CancellationToken token) {
            List<ListOrDictionary> afterUnion = DoListUnions(ids, token);
            if (afterUnion == null) return null;
            List<Filename> afterMiltiplication = DoListMultiplications(afterUnion, token);
            if (afterMiltiplication == null) return null;

            List<Thumbnail> thumbnails = new List<Thumbnail>();

            foreach (var item in afterMiltiplication) {
                if (token.IsCancellationRequested) return null;
                thumbnails.Add(new Thumbnail() { Filename = item, Image = GetImage(item.Id) });
            }
            return thumbnails;
        }

        private void UpdateThumbnails(List<Thumbnail> thumbnails) {
            ItemsControl.ItemsSource = thumbnails;
            HideNotFoundMessageBox();
        }

        private List<Filename> DoListMultiplications(List<ListOrDictionary> lists, CancellationToken token) {
            if (lists.Count == 1 && lists[0].List != null)
                return lists[0].List;

            Dictionary<uint, Filename> dict = null;
            for (int i = 0; i < lists.Count; i++) {
                if (lists[i].Dictionary != null) {
                    dict = lists[i].Dictionary;
                    lists.RemoveAt(i);
                    break;
                }
            }
            if (dict == null) {
                dict = lists[lists.Count - 1].List.ToDictionary(f => f.Id);
                lists.RemoveAt(lists.Count - 1);
            }

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

            foreach (var item in dict) {
                list.Add(item.Value);
            }
            list.Sort();
            return list;
        }

        private struct ListOrDictionary {
            public List<Filename> List;
            public Dictionary<uint, Filename> Dictionary;
        }

        private List<ListOrDictionary> DoListUnions(List<List<int>> ids, CancellationToken token) {
            var list = new List<ListOrDictionary>();

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
                        ShowNotFoundMessageBox(NotFoundMessageType.InvalidFormat, filter);
                        return null;
                    }

                    if (!LabelProvider.Labels.TryGetValue(cls, out label)) {
                        ShowNotFoundMessageBox(NotFoundMessageType.InvalidLabel, cls);
                        return null;
                    }
                    if (!Classes.ContainsKey(label.Id)) continue;

                    list[p].Add(label.Id);
                }
            }
            for (int p = 0; p < list.Count; p++) {
                if (list[p].Count == 0) {
                    ShowNotFoundMessageBox(NotFoundMessageType.NotFound, parts[p]);
                    return null;
                }
            }
            return list;
        }

        enum NotFoundMessageType { NotFound, InvalidLabel, InvalidFormat, ResourcesNotLoadedYet }
        NotFoundMessageConverter NotFoundMessageConverter = new NotFoundMessageConverter();

        private void ShowNotFoundMessageBox(NotFoundMessageType type, string message) {
            switch (type) {
                case NotFoundMessageType.NotFound:
                    NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                        new string[] { "No images of ", " found" },
                        CultureInfo.CurrentCulture);
                    break;
                case NotFoundMessageType.InvalidLabel:
                    NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                        new string[] { "Label ", " does not exist" },
                        CultureInfo.CurrentCulture);
                    break;
                case NotFoundMessageType.InvalidFormat:
                    NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                        new string[] { "Input ", " is incorrectly formated" },
                        CultureInfo.CurrentCulture);
                    break;
                case NotFoundMessageType.ResourcesNotLoadedYet:
                    NotFoundMessageBox.Content = NotFoundMessageConverter.Convert("", null,
                        new string[] { "Labels or index file not loaded yet", "" },
                        CultureInfo.CurrentCulture);
                    break;
                default:
                    break;
            }

            NotFoundMessageBox.Visibility = Visibility.Visible;
            if (ItemsControl != null)
                ItemsControl.ItemsSource = null;
        }
        private void HideNotFoundMessageBox() {
            NotFoundMessageBox.Visibility = Visibility.Hidden;
        }
    }
}
