using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CustomElements {
    public interface ISearchProvider {
        void Search(string filter, SuggestionTextBox suggestionTextBox);
    }
}
