using System;
using System.Collections;

namespace CustomElements {

    public interface ISuggestionProvider {
        void GetSuggestionsAsync(string filter, SuggestionTextBox suggestionTextBox);
        void CancelSuggestionsLookup();
    }

}
