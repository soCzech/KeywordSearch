
namespace CustomElements {

    /// <summary>
    /// Interface for each suggestion item, providing the actual text to write in a seach box
    /// </summary>
    public interface IIdentifiable {
        /// <summary>
        /// </summary>
        /// <returns>Text to be writen into a search box</returns>
        string GetTextRepresentation();
    }

}
