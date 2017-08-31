using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using KeywordSearchInterface;

namespace KeywordSearch {
    class SuggestionTemplateSelector : DataTemplateSelector {
        public DataTemplate Hypernym { get; set; }
        public DataTemplate Both { get; set; }
        public DataTemplate Class { get; set; }

        public override DataTemplate SelectTemplate(object item, DependencyObject container) {
            if (((ImageClass)item).IsHypernym)
                return Hypernym;
            else if (((ImageClass)item).Hyponyms != null)
                return Both;
            return Class;
        }
    }
}
