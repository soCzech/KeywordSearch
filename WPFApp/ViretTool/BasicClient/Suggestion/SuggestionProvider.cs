using System;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.Threading.Tasks;
using System.Threading;
using ViretTool.Utils;
using ViretTool.BasicClient.Controls;

namespace ViretTool.BasicClient.Suggestion {

    class SuggestionProvider {

        private LabelProvider mLabelProvider;

        private CancellationTokenSource CTS;
        
        /// <param name="labelProvider">Reference to a class managing suggestion dictionary</param>
        public SuggestionProvider(LabelProvider labelProvider) {
            mLabelProvider = labelProvider;
        }

        #region Events

        public delegate void SuggestionResultsReadyHandler(IEnumerable<IIdentifiable> suggestions, string filter);
        /// <summary>
        /// Called when new result are ready and should be shown
        /// </summary>
        public event SuggestionResultsReadyHandler SuggestionResultsReadyEvent;

        public delegate void ShowSuggestionMessageHandler(string message);
        /// <summary>
        /// Called when an UI message should be shown
        /// </summary>
        public event ShowSuggestionMessageHandler ShowSuggestionMessageEvent;

        #endregion

        #region Interface Methods

        public IEnumerable<IIdentifiable> GetSuggestions(IEnumerable<int> withClasses, string filter) {
            List<IIdentifiable> list = new List<IIdentifiable>();

            if (!mLabelProvider.LoadTask.IsFaulted && mLabelProvider.LoadTask.IsCompleted) {
                // build Aho-Corasick trie
                AhoCorasick AC = new AhoCorasick();
                AC.Add(filter);
                AC.Build();

                foreach (var item in withClasses) {
                    Label l = mLabelProvider.Labels[item];

                    SuggestionResultItem iCls = LabelToListItem(l, AC, true);
                    list.Add(iCls);
                }
            }
            return list;
        }

        /// <summary>
        /// Checks if labels are loaded. Creates new task that searches for correct labels. Calls <see cref="SuggestionResultsReadyEvent"/>.
        /// </summary>
        /// <param name="filter">A string the result should be for</param>
        public void GetSuggestionsAsync(string filter) {
            if (mLabelProvider.LoadTask.IsFaulted) {
                ShowSuggestionMessageEvent(mLabelProvider.LoadTask.Exception.InnerException.Message);
                return;
            } else if (!mLabelProvider.LoadTask.IsCompleted) {
                ShowSuggestionMessageEvent("Labels not loaded yet...");
                return;
            } else {
                ShowSuggestionMessageEvent("Loading...");
            }

            CTS = new CancellationTokenSource();

            Task.Factory.StartNew(() => { return GetList(filter, CTS.Token); },
                CTS.Token, TaskCreationOptions.None, TaskScheduler.Default).ContinueWith((Task<IEnumerable<IIdentifiable>> task) => {
                    if (task.IsFaulted) {
                        ShowSuggestionMessageEvent(task.Exception.InnerException.Message);
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

                if (filter == string.Empty) return new List<SuggestionResultItem>();
            }

            // build Aho-Corasick trie
            AhoCorasick AC = new AhoCorasick();
            AC.Add(filter);
            AC.Build();

            var list = new List<SuggestionResultItem>();
            // iterate over all the labels
            foreach (var kvp in mLabelProvider.Labels) {
                var item = kvp.Value;
                // stop if search canceled
                if (token.IsCancellationRequested) {
                    break;
                }

                SuggestionResultItem iCls = LabelToListItem(item, AC);
                if (iCls != null) {
                    //iCls.TextRepresentation = keepPart + iCls.TextRepresentation;
                    list.Add(iCls);
                }
            }
            if (!token.IsCancellationRequested)
                list.Sort();

            return list;
        }


        private SuggestionResultItem LabelToListItem(Label item, AhoCorasick AC, bool showAll = false) {
            // search in label name
            var nameEnum = AC.Find(item.Name);
            // search in description
            var descriptionEnum = AC.Find(item.Description);

            if (showAll || nameEnum.Any() || descriptionEnum.Any()) {
                // highlight the search phrase in the text and calculate relevance of the search
                var nameRel = HighlightAndRankPhrase(nameEnum, item.Name);
                var descriptionRel = HighlightAndRankPhrase(descriptionEnum, item.Description);

                string[] hyponymNames = null;
                if (item.Hyponyms != null) {
                    hyponymNames = new string[item.Hyponyms.Length];

                    Label l;
                    for (int i = 0; i < item.Hyponyms.Length; i++) {
                        l = mLabelProvider.Labels[item.Hyponyms[i]];
                        hyponymNames[i] = l.Names[0];
                    }
                }

                return new SuggestionResultItem {
                    Label = item,
                    Name = nameRel.HighlightedString,
                    Hyponyms = hyponymNames == null ? null : string.Join(", ", hyponymNames),
                    Description = descriptionRel.HighlightedString,
                    SearchRelevance = new SuggestionResultItem.Relevance() {
                        NameHits = nameRel.Hits,
                        DescriptionHits = descriptionRel.Hits,
                        Bonus = nameRel.Bonus
                    }
                };
            }
            return null;
        }

        private struct HighlightedStringWithRelevance {
            public string HighlightedString { get; set; }
            public byte Hits { get; set; }
            public SuggestionResultItem.Relevance.NameBonus Bonus { get; set; }
        }

        /// <summary>
        /// Calculates relevance of the search phrase in the text. Encapsulates search phrases in the text by <see cref="SuggestionResultItem.HIGHLIGHT_START_TAG"/> and <see cref="SuggestionResultItem.HIGHLIGHT_END_TAG"/>.
        /// </summary>
        /// <param name="hits">An enunerable of results from the Aho-Corasick search</param>
        /// <param name="text">A string the highlighting is done on</param>
        /// <returns></returns>
        private HighlightedStringWithRelevance HighlightAndRankPhrase(IEnumerable<AhoCorasick.Occurrence> hits, string text) {
            int startsAt = 0;
            byte count = 0;

            SuggestionResultItem.Relevance.NameBonus bonus = SuggestionResultItem.Relevance.NameBonus.None;

            StringBuilder builder = new StringBuilder();
            foreach (var item in hits) {
                if (item.StartsAt < startsAt) continue;
                if (bonus == SuggestionResultItem.Relevance.NameBonus.None) {
                    // adds a bonus if the text starts with the search phrase
                    if (item.StartsAt == 0) {
                        if (item.Word.Length == text.Length) bonus = SuggestionResultItem.Relevance.NameBonus.FullNameAlone;
                        else if (text[item.Word.Length] == ',') bonus = SuggestionResultItem.Relevance.NameBonus.FullName;
                        else if (!text.Contains(',')) bonus = SuggestionResultItem.Relevance.NameBonus.StartsNameAlone;
                        else bonus = SuggestionResultItem.Relevance.NameBonus.StartsName;
                    } else if (text[(int)item.StartsAt - 1] == ' ') bonus = SuggestionResultItem.Relevance.NameBonus.StartsWord;
                }
                count++;

                builder.Append(text.Substring(startsAt, (int)(item.StartsAt - startsAt)));
                builder.Append(StringHighlightingConverter.HIGHLIGHT_START_TAG);
                builder.Append(text.Substring((int)item.StartsAt, item.Word.Length));
                builder.Append(StringHighlightingConverter.HIGHLIGHT_END_TAG);
                startsAt = (int)item.StartsAt + item.Word.Length;
            }
            builder.Append(text.Substring(startsAt));

            return new HighlightedStringWithRelevance() { HighlightedString = builder.ToString(), Hits = count, Bonus = bonus };
        }

        #endregion

    }

}
