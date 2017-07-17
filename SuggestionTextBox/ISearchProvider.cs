using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CustomElements {
    /// <summary>
    /// Interface for a provider of results based on search phrase
    /// </summary>
    public interface ISearchProvider {
        /// <summary>
        /// Called when user searches from a search box
        /// </summary>
        /// <param name="filter">A string the result should be for</param>
        /// <param name="suggestionTextBox">A reference to the search box</param>
        void Search(string filter, SuggestionTextBox suggestionTextBox);
    }
}
