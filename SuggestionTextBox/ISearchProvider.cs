
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

        /// <summary>
        /// Called when search results not needed
        /// </summary>
        void CancelSearch();
    }

}
