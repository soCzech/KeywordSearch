using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Media;

namespace ViretTool.BasicClient.Controls {
    class QueryTextBlock : TextBlock, IQueryPart {
        public int Id { get; private set; }

        private TextBlockType type;
        public TextBlockType Type {
            get {
                return type;
            }
            set {
                if (value == TextBlockType.Class) return;
                type = value;
            }
        }
        public bool UseChildren { get; private set; }

        public QueryTextBlock(IIdentifiable item, bool ctrlKey) {
            Type = TextBlockType.Class;
            Text = item.TextRepresentation;
            Id = item.Id;
            UseChildren = (!ctrlKey && item.HasChildren) || item.HasOnlyChildren;

            if (UseChildren) {
                if (item.HasOnlyChildren) {
                    ToolTip = string.Format("{0}\nid: {1}\nHypernym", item.TextDescription, item.Id);
                    Background = Brushes.LightPink;
                } else {
                    ToolTip = string.Format("{0}\nid: {1}\nHypernym (hold Ctrl when selecting to use only {2})", item.TextDescription, item.Id, item.TextRepresentation);
                    Background = Brushes.LightGreen;
                }
            } else {
                ToolTip = string.Format("{0}\nid: {1}", item.TextDescription, item.Id);
            }
        }

        public QueryTextBlock(TextBlockType type) {
            if (type == TextBlockType.Class) throw new Exception();

            Type = type;
            Text = type == TextBlockType.AND ? "AND" : "OR";
            ToolTip = "Click to change logical operator";
            Foreground = Brushes.Red;
        }
    }
}
