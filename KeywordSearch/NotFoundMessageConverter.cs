using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security;
using System.Text;
using System.Threading.Tasks;

using System.Windows.Data;
using System.Windows.Markup;
using System.Xml;

namespace KeywordSearch {

    [ValueConversion(typeof(string), typeof(object))]
    sealed class NotFoundMessageConverter : IValueConverter {

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture) {
            string input = value as string;
            if (input == null && value != null) return null;

            if (input == string.Empty)
                input = "<Run Foreground=\"Gray\">Nothing to show</Run>";
            else if (value == null)
                input = "<Run Foreground=\"Gray\">Labels or index file not loaded yet</Run>";
            else {
                string escaped = SecurityElement.Escape(input);
                StringBuilder builder = new StringBuilder();
                foreach (char c in escaped) {
                    if (c == '+' || c == '*') {
                        builder.Append("<Run Foreground=\"Red\">");
                        builder.Append(c == '*' ? '\u00d7' : c);
                        builder.Append("</Run>");
                    } else {
                        builder.Append(c);
                    }
                }
                builder.Append(" <Run Foreground=\"Gray\">not found</Run>");
                input = builder.ToString();
            }
            
            string wrappedXml = string.Format("<TextBlock TextAlignment=\"Center\" xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" xml:space=\"preserve\" TextWrapping=\"Wrap\">{0}</TextBlock>", input);

            using (StringReader stringReader = new StringReader(wrappedXml)) {
                using (XmlReader xmlReader = XmlReader.Create(stringReader)) {
                    return XamlReader.Load(xmlReader);
                }
            }
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) {
            throw new NotImplementedException("The converter does not support two-way binding.");
        }
    }
}
