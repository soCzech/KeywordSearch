using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.BasicClient.Controls {

    /// <summary>
    /// Interface for each suggestion item, providing the actual text to write in a seach box
    /// </summary>
    interface IIdentifiable {

        /// <summary>
        /// </summary>
        /// <returns>Class ID of the text representation</returns>
        int Id { get; }

        /// <summary>
        /// </summary>
        /// <returns>Text to be writen into a search box</returns>
        string TextRepresentation { get; }
        string TextDescription { get; }

        bool HasChildren { get; }
        bool HasOnlyChildren { get; }

        IEnumerable<int> Children { get; }
    }

}
