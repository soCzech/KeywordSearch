using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace ViretTool.BasicClient.Controls {
    class SuggestionTemplateSelector : DataTemplateSelector {
        public DataTemplate OnlyChildren { get; set; }
        public DataTemplate WithChildren { get; set; }
        public DataTemplate Base { get; set; }

        public override DataTemplate SelectTemplate(object item, DependencyObject container) {
            if (((IIdentifiable)item).HasOnlyChildren)
                return OnlyChildren;
            else if (((IIdentifiable)item).HasChildren)
                return WithChildren;
            return Base;
        }
    }
}
