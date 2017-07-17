using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace KeywordSearch {

    class Label : IComparable<Label> {
        public int Id { get; set; }
        public string SynsetId { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public int NameLenghtInWords { get; set; }

        public int CompareTo(Label other) {
            return Name.CompareTo(other.Name);
        }
    }

}
