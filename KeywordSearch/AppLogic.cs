using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace KeywordSearch {

    /// <summary>
    /// Class holding all the logic.
    /// </summary>
    public class AppLogic {
        internal LabelProvider LabelProvider;
        internal SuggestionProvider SuggestionProvider;
        internal ImageProvider ImageProvider;

        public AppLogic() {
            LabelProvider = new LabelProvider();
            SuggestionProvider = new SuggestionProvider(LabelProvider);
            ImageProvider = new ImageProvider(LabelProvider);
        }

    }
}
