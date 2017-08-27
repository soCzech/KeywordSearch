using System;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.Threading.Tasks;
using System.Threading;
using CustomElements;

namespace KeywordSearchInterface {

    public class SuggestionProvider : ISuggestionProvider {

        private LabelProvider LabelProvider;
        private CancellationTokenSource CTS;

        /// <param name="labelProvider">Reference to a class managing suggestion dictionary</param>
        public SuggestionProvider(LabelProvider labelProvider) {
            LabelProvider = labelProvider;
        }

        #region Events

        /// <summary>
        /// Delegate for <see cref="SuggestionResultsReadyEvent"/>
        /// </summary>
        public delegate void SuggestionResultsReady(IEnumerable<IIdentifiable> suggestions, string filter);

        /// <summary>
        /// Called when new result are ready and should be shown
        /// </summary>
        public event SuggestionResultsReady SuggestionResultsReadyEvent;

        /// <summary>
        /// Delegate for <see cref="ShowSuggestionMessageEvent"/>
        /// </summary>
        /// <param name="type">Type of an message</param>
        /// <param name="message">A text the message to show</param>
        public delegate void ShowSuggestionMessage(SuggestionMessageType type, string message);

        /// <summary>
        /// Called when an UI message should be shown
        /// </summary>
        public event ShowSuggestionMessage ShowSuggestionMessageEvent;

        #endregion

        #region Interface Methods

        /// <summary>
        /// Checks if labels are loaded. Creates new task that searches for correct labels. Calls <see cref="SuggestionResultsReadyEvent"/>.
        /// </summary>
        /// <param name="filter">A string the result should be for</param>
        public void GetSuggestions(string filter) {
            if (LabelProvider.LoadTask.IsFaulted) {
                ShowSuggestionMessageEvent(SuggestionMessageType.Exception, LabelProvider.LoadTask.Exception.InnerException.Message);
                return;
            } else if (!LabelProvider.LoadTask.IsCompleted) {
                ShowSuggestionMessageEvent(SuggestionMessageType.ResourcesNotLoadedYet, "Labels not loaded yet...");
                return;
            } else {
                ShowSuggestionMessageEvent(SuggestionMessageType.ResourcesNotLoadedYet, "Loading...");
            }

            CTS = new CancellationTokenSource();

            Task.Factory.StartNew(() => { return GetList(filter, CTS.Token); },
                CTS.Token, TaskCreationOptions.None, TaskScheduler.Default).ContinueWith((Task<IEnumerable<IIdentifiable>> task) => {
                    if (task.IsFaulted) {
                        ShowSuggestionMessageEvent(SuggestionMessageType.Exception, task.Exception.InnerException.Message);
                        return;
                    }

                    SuggestionResultsReadyEvent(task.Result, filter);
            }, CTS.Token, TaskContinuationOptions.NotOnCanceled, TaskScheduler.Default);
        }

        /// <summary>
        /// Calls Cancel() on <see cref="CancellationTokenSource">CancellationTokenSource</see> resulting in cancelation of a label search task.
        /// </summary>
        public void CancelSuggestions() {
            CTS?.Cancel();
        }

        #endregion

        #region Private Search Methods

        /// <summary>
        /// Performs the search on all labels
        /// </summary>
        /// <param name="filter">A string the result should be for</param>
        /// <param name="token">A cancellation token to stop the search if necessary</param>
        /// <returns></returns>
        private IEnumerable<IIdentifiable> GetList(string filter, CancellationToken token) {
            // find last part of the search string (castle+tree*human -> human)
            // do the suggestions only on the last part
            int lastPart = Math.Max(filter.LastIndexOf('+'), filter.LastIndexOf('*')) + 1;
            string keepPart = string.Empty;

            if (lastPart != 0) {
                keepPart = filter.Substring(0, lastPart);
                filter = filter.Substring(lastPart).Trim();

                if (filter == string.Empty) return new List<ImageClass>();
            }

            // build Aho-Corasick trie
            AhoCorasick AC = new AhoCorasick();
            AC.Add(filter);
            AC.Build();

            var list = new List<ImageClass>();
            // iterate over all the labels
            foreach (var kvp in LabelProvider.Labels) {
                var item = kvp.Value;
                // stop if search canceled
                if (token.IsCancellationRequested) {
                    break;
                }

                // search in label name
                var nameEnum = AC.Find(item.Name);
                // search in description
                var descriptionEnum = AC.Find(item.Description);

                if (nameEnum.Any() || descriptionEnum.Any()) {
                    // highlight the search phrase in the text and calculate relevance of the search
                    var nameRel = HighlightPhrase(nameEnum, item.Name);
                    var descriptionRel = HighlightPhrase(descriptionEnum, item.Description);

                    if (item.Id != -1) {
                        list.Add(new ImageClass {
                            IsHypernym = false,
                            SearchableName = keepPart + item.Name,
                            Name = nameRel.HighlightedString,
                            Description = descriptionRel.HighlightedString,
                            NameLenghtInWords = item.NameLenghtInWords,
                            SearchRelevance = new Relevance() { NameHits = nameRel.Hits, DescriptionHits = descriptionRel.Hits, Bonus = nameRel.Bonus }
                        });
                    } else {
                        var printNames = new string[item.Hyponyms.Length];
                        for (int i = 0; i < item.Hyponyms.Length; i++) {
                            printNames[i] = LabelProvider.Labels[item.Hyponyms[i]].Name;
                        }
                        list.Add(new ImageClass {
                            IsHypernym = true,
                            SearchableName = keepPart + string.Join("+", printNames),
                            Name = nameRel.HighlightedString,
                            Description = descriptionRel.HighlightedString,
                            NameLenghtInWords = item.NameLenghtInWords,
                            SearchRelevance = new Relevance() { NameHits = nameRel.Hits, DescriptionHits = descriptionRel.Hits, Bonus = nameRel.Bonus }
                        });
                    }
                }
            }
            if (!token.IsCancellationRequested)
                list.Sort();

            return list;
        }

        /// <summary>
        /// Calculates relevance of the search phrase in the text. Encapsulates search phrases in the text by <see cref="StringHighlightingConverter.START_TAG"/> and <see cref="StringHighlightingConverter.END_TAG"/>.
        /// </summary>
        /// <param name="hits">An enunerable of results from the Aho-Corasick search</param>
        /// <param name="text">A string the highlighting is done on</param>
        /// <returns></returns>
        private HighlightedStringWithRelevance HighlightPhrase(IEnumerable<Occurrence> hits, string text) {
            int startsAt = 0;
            byte count = 0;
            NameBonus bonus = NameBonus.None;

            StringBuilder builder = new StringBuilder();
            foreach (var item in hits) {
                if (item.StartsAt < startsAt) continue;
                if (bonus == NameBonus.None) {
                    // adds a bonus if the text starts with the search phrase
                    if (item.StartsAt == 0) {
                        if (item.Word.Length == text.Length) bonus = NameBonus.FullNameAlone;
                        else if (text[item.Word.Length] == ',') bonus = NameBonus.FullName;
                        else if (!text.Contains(',')) bonus = NameBonus.StartsNameAlone;
                        else bonus = NameBonus.StartsName;
                    } else if (text[(int)item.StartsAt - 1] == ' ') bonus = NameBonus.StartsWord;
                }
                count++;

                builder.Append(text.Substring(startsAt, (int)(item.StartsAt - startsAt)));
                builder.Append(StringHighlightingConverter.START_TAG);
                builder.Append(text.Substring((int)item.StartsAt, item.Word.Length));
                builder.Append(StringHighlightingConverter.END_TAG);
                startsAt = (int)item.StartsAt + item.Word.Length;
            }
            builder.Append(text.Substring(startsAt));

            return new HighlightedStringWithRelevance() { HighlightedString = builder.ToString(), Hits = count, Bonus = bonus };
        }

        private struct HighlightedStringWithRelevance {
            public string HighlightedString { get; set; }
            public byte Hits { get; set; }
            public NameBonus Bonus { get; set; }
        }

        #endregion

    }

}
