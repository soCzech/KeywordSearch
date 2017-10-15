using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CustomElements;
using KeywordSearchInterface;

namespace KeywordSearch {
    class KeywordSearchController {

        private Dictionary<string, LabelProvider> mLabelProviders = new Dictionary<string, LabelProvider>();
        private Dictionary<string, SuggestionProvider> mSuggestionProviders = new Dictionary<string, SuggestionProvider>();
        private Dictionary<string, ImageProvider> mImageProviders = new Dictionary<string, ImageProvider>();

        private SuggestionTextBox mSuggestionTextBox;

        //public delegate void SuggestionFilterChangedHandler(string filter, string annotationSource);
        //public event SuggestionFilterChangedHandler SuggestionFilterChangedEvent;


        public event ImageProvider.KeywordResultsReadyHandler KeywordResultsReadyEvent;
        public event ImageProvider.ShowSearchMessage ShowSearchMessageEvent;

        public KeywordSearchController(SuggestionTextBox suggestionTextBox, string[] annotationSources) {
            mSuggestionTextBox = suggestionTextBox;
            mSuggestionTextBox.AnnotationSources = annotationSources;

            foreach (string source in annotationSources) {

                var labelProvider = new LabelProvider(source + ".labels");
                mLabelProviders.Add(source, labelProvider);

                var suggestionProvider = new SuggestionProvider(labelProvider);
                mSuggestionProviders.Add(source, suggestionProvider);
                suggestionProvider.SuggestionResultsReadyEvent += SuggestionProvider_SuggestionResultsReadyEvent;
                suggestionProvider.ShowSuggestionMessageEvent += SuggestionProvider_ShowSuggestionMessageEvent;

                var imageProvider = new ImageProvider(labelProvider, source + ".index");
                mImageProviders.Add(source, imageProvider);
                imageProvider.ShowSearchMessageEvent += ImageProvider_ShowSearchMessageEvent;
                imageProvider.KeywordResultsReadyEvent += ImageProvider_KeywordResultsReadyEvent; ;
            }

            mSuggestionTextBox.QueryChangedEvent += SuggestionTextBox_QueryChangedEvent;
            mSuggestionTextBox.SuggestionFilterChangedEvent += SuggestionTextBox_SuggestionFilterChangedEvent;
            mSuggestionTextBox.SuggestionsNotNeededEvent += SuggestionTextBox_SuggestionsNotNeededEvent;
            mSuggestionTextBox.GetSuggestionSubtreeEvent += SuggestionTextBox_GetSuggestionSubtreeEvent;
        }

        private void ImageProvider_KeywordResultsReadyEvent(List<Filename> filenames) {
            KeywordResultsReadyEvent(filenames);
        }

        private void ImageProvider_ShowSearchMessageEvent(SearchMessageType type, string message) {
            ShowSearchMessageEvent(type, message);
        }

        private void SuggestionProvider_ShowSuggestionMessageEvent(SuggestionMessageType type, string message) {
            mSuggestionTextBox.OnShowSuggestionMessage(type, message);
        }

        private void SuggestionProvider_SuggestionResultsReadyEvent(IEnumerable<IIdentifiable> suggestions, string filter) {
            mSuggestionTextBox.OnSuggestionResultsReady(suggestions, filter);
        }




        private IEnumerable<IIdentifiable> SuggestionTextBox_GetSuggestionSubtreeEvent(IEnumerable<int> subtree, string filter, string annotationSource) {
            return mSuggestionProviders[annotationSource].GetSuggestions(subtree, filter);
        }

        private void SuggestionTextBox_SuggestionsNotNeededEvent() {
            foreach (KeyValuePair<string,SuggestionProvider> provider in mSuggestionProviders) {
                provider.Value.CancelSuggestions();
            }
        }

        private void SuggestionTextBox_SuggestionFilterChangedEvent(string filter, string annotationSource) {
            mSuggestionProviders[annotationSource].GetSuggestions(filter);
        }

        private void SuggestionTextBox_QueryChangedEvent(IEnumerable<IQueryPart> query, string annotationSource) {
            mImageProviders[annotationSource].Search(query);
        }

    }
}
