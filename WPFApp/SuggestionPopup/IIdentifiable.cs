
using System.Collections.Generic;

namespace CustomElements {

    /// <summary>
    /// Interface for each suggestion item, providing the actual text to write in a seach box
    /// </summary>
    public interface IIdentifiable {
        /// <summary>
        /// </summary>
        /// <returns>Text to be writen into a search box</returns>
        string TextRepresentation { get; }
        string TextDescription { get; }

        /// <summary>
        /// </summary>
        /// <returns>Class ID of the text representation</returns>
        int Id { get; }

        bool HasChildren { get; }
        bool HasOnlyChildren { get; }

        IEnumerable<int> Children { get; }
    }

}
