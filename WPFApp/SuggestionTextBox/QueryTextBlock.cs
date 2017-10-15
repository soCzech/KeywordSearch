using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace CustomElements {
    public class QueryTextBlock : TextBlock {
        public int Id { get; private set; }
        public TextBlockType Type { get; private set; }

        public QueryTextBlock(string shortText, string longText, int id) {
            Type = TextBlockType.Class;
            Text = shortText;
            ToolTip = string.Format("{0}\nid: {1}", longText, id);
            Id = id;
        }

        public QueryTextBlock(TextBlockType type) {
            if (type == TextBlockType.Class) throw new Exception();

            Type = type;
            Text = type == TextBlockType.AND ? "AND" : "OR";
            ToolTip = "Click to change logical operator";
            Foreground = Brushes.Red;

            MouseUp += QueryTextBlock_MouseUp;
        }

        private void QueryTextBlock_MouseUp(object sender, System.Windows.Input.MouseButtonEventArgs e) {
            Type = Type == TextBlockType.AND ? TextBlockType.OR : TextBlockType.AND;
            Text = Type == TextBlockType.AND ? "AND" : "OR";
        }
    }
    public enum TextBlockType { Class, OR, AND }
}