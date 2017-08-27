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
        void Search(string filter);

        void CancelSearch();
    }

    public enum ErrorMessageType { Exception, NotFound, InvalidLabel, InvalidFormat, ResourcesNotLoadedYet }

    /// <summary>
    /// Show error message in UI.
    /// </summary>
    /// <param name="type">Type of an error</param>
    /// <param name="message">A text the error is in</param>
    public delegate void SearchError(ErrorMessageType type, string message);
}
