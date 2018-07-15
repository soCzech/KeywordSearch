using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.BasicClient.Suggestion {

    /// <summary>
    /// Representation of a WordNet synset in this tool
    /// </summary>
    class Label : IComparable<Label> {
        /// <summary>
        /// Id in an inverted index (neural network)
        /// </summary>
        public int Id { get; set; }
        /// <summary>
        /// WordNet synset id
        /// </summary>
        public int SynsetId { get; set; }
        /// <summary>
        /// Text representation of a label
        /// </summary>
        public string Name { get; set; }
        /// <summary>
        /// List of all label's names in WordNet
        /// </summary>
        public string[] Names { get; set; }
        /// <summary>
        /// List of label's hyponyms (WordNet synset ids)
        /// </summary>
        public int[] Hyponyms { get; set; }
        /// <summary>
        /// List of label's hypernyms (WordNet synset ids)
        /// </summary>
        public int[] Hypernyms { get; set; }
        /// <summary>
        /// Description of a label from WordNet
        /// </summary>
        public string Description { get; set; }
        /// <summary>
        /// Minimal length of one of the <see cref="Names"/>
        /// </summary>
        public int NameLenghtInWords { get; set; }

        public int CompareTo(Label other) {
            return Name.CompareTo(other.Name);
        }
    }

}
