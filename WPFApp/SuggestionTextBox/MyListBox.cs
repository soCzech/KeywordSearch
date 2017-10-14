using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace CustomElements {
    public class MyListBox : ListBox{

        public override void OnApplyTemplate() {
            base.OnApplyTemplate();

            ScrollViewer x = FindVisualChild<ScrollViewer>(this);
            x.HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled;
            x.VerticalScrollBarVisibility = ScrollBarVisibility.Hidden;
        }

        private childItem FindVisualChild<childItem>(DependencyObject obj) where childItem : DependencyObject {
            for (int i = 0; i < VisualTreeHelper.GetChildrenCount(obj); i++) {
                DependencyObject child = VisualTreeHelper.GetChild(obj, i);

                if (child != null && child is childItem) {
                    return (childItem)child;
                } else {
                    childItem childOfChild = FindVisualChild<childItem>(child);
                    if (childOfChild != null)
                        return childOfChild;
                }
            }
            return null;
        }
    }
}