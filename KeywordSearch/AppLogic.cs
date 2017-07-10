using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace KeywordSearch {
    public class AppLogic {
        internal LabelProvider LabelProvider;
        internal SuggestionProvider SuggestionProvider;

        public AppLogic() {
            LabelProvider = new LabelProvider();
            SuggestionProvider = new SuggestionProvider(LabelProvider);
        }


    }
}
