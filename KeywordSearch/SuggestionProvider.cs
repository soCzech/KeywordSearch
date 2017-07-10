using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.Threading.Tasks;
// !
using CustomElements;
using System.Diagnostics;
using System.Windows.Controls;
using System.Threading;

using KeywordSearch.TextSearch;

namespace KeywordSearch {
    class SuggestionProvider : ISuggestionProvider {

        private LabelProvider LabelProvider;
        private CancellationTokenSource CTS;

        public SuggestionProvider(LabelProvider labelProvider) {
            LabelProvider = labelProvider;
        }

        public void GetSuggestionsAsync(string filter, SuggestionTextBox suggestionTextBox) {
            if (!LabelProvider.LoadTask.IsCompleted) {
                ((TextBlock)suggestionTextBox.LoadingPlaceholder).Text = "Labels not loaded yet...";
                return;
            } else {
                ((TextBlock)suggestionTextBox.LoadingPlaceholder).Text = "Loading...";
            }

            CTS = new CancellationTokenSource();

            Task.Factory.StartNew(() => { return GetList(filter, CTS.Token); },
                CTS.Token, TaskCreationOptions.None, TaskScheduler.Default).ContinueWith((Task<IEnumerable<IIdentifiable>> task) => {
                    
                    suggestionTextBox.Dispatcher.BeginInvoke(
                        new Action<IEnumerable<IIdentifiable>, string>(suggestionTextBox.OnSuggestionUpdate),
                        new object[] { task.Result, filter }
                        );
            }, CTS.Token, TaskContinuationOptions.NotOnCanceled, TaskScheduler.Default);
        }

        public void CancelSuggestionsLookup() {
            CTS?.Cancel();
        }

        private IEnumerable<IIdentifiable> GetList(string filter, CancellationToken token) {
            int lastPart = Math.Max(filter.LastIndexOf('+'), filter.LastIndexOf('*')) + 1;
            string keepPart = string.Empty;

            if (lastPart != 0) {
                keepPart = filter.Substring(0, lastPart);
                filter = filter.Substring(lastPart).Trim();

                if (filter == string.Empty) return null;
            }

            AhoCorasick AC = new AhoCorasick();
            AC.Add(filter);
            AC.Build();

            var list = new List<ImageClass>();
            foreach (var item in LabelProvider.Labels) {
                if (token.IsCancellationRequested) {
                    break;
                }

                var nameEnum = AC.Find(item.Name);
                var descriptionEnum = AC.Find(item.Description);

                if (nameEnum.Any() || descriptionEnum.Any()) {
                    var nameRel = HighlightPhrase(nameEnum, item.Name);
                    var descriptionRel = HighlightPhrase(descriptionEnum, item.Description);

                    list.Add(new ImageClass {
                        SearchableName = keepPart + item.Name,
                        Name = nameRel.HighlightedString,
                        Description = descriptionRel.HighlightedString,
                        NameLenghtInWords = item.NameLenghtInWords,
                        SearchRelevance = new Relevance() { NameHits = nameRel.Hits, DescriptionHits = descriptionRel.Hits, Bonus = nameRel.Bonus }
                    });
                }
            }
            list.Sort();

            return list;
        }

        private HighlightedStringWithRelevance HighlightPhrase(IEnumerable<Occurrence> hits, string text) {
            int startsAt = 0;
            byte count = 0;
            NameBonus bonus = NameBonus.None;

            StringBuilder builder = new StringBuilder();
            foreach (var item in hits) {
                if (item.StartsAt < startsAt) continue;
                if (bonus == NameBonus.None) {
                    if (item.StartsAt == 0) {
                        if (item.Word.Length == text.Length || text[item.Word.Length] == ',') bonus = NameBonus.FullName;
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
    }
}
