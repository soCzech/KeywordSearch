
using System.Collections.Generic;

namespace CustomElements {

    /// <summary>
    /// Interface providing suggestions for the search box
    /// </summary>
    public interface ISuggestionProvider {
        /// <summary>
        /// Shall create the suggestions as IEnumerable&lt;IIdentifiable&gt;.
        /// To update the list, call OnSuggestionUpdate(IEnumerable&lt;IIdentifiable&gt; suggestions, string filter).
        /// Second argument filter should be the same as the input argument.
        /// </summary>
        /// <param name="filter">A string the suggestions should be for</param>
        void GetSuggestions(string filter);

        IEnumerable<IIdentifiable> GetSuggestions(IEnumerable<int> withClasses, string filter);
        /// <summary>
        /// Called to stop any ongoing suggestions search (eg. the filter argument changed).
        /// </summary>
        void CancelSuggestions();
    }

}
