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

    /// <summary>
    /// Converts string to WPF TextBlock to be shown as error.
    /// </summary>
    [ValueConversion(typeof(string), typeof(object))]
    sealed class NotFoundMessageConverter : IValueConverter {

        /// <summary>
        /// 
        /// </summary>
        /// <param name="value">A string to be in black with red + and *</param>
        /// <param name="targetType">Not used</param>
        /// <param name="parameter">A string[] of length 2 with text preceeding and following the value argument in grey</param>
        /// <param name="culture">Not used</param>
        /// <returns>WPF TextBlock to be shown as error</returns>
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture) {
            string input = value as string;
            string[] array = parameter as string[]; ;

            if (input == null || array == null || array.Length != 2) return null;

            string escaped = SecurityElement.Escape(input);
            StringBuilder builder = new StringBuilder();
            builder.Append(string.Format("<Run Foreground=\"Gray\">{0}</Run>", array[0]));

            foreach (char c in escaped) {
                if (c == '+' || c == '*') {
                    builder.Append("<Run Foreground=\"Red\">");
                    builder.Append(c == '*' ? '\u00d7' : c);
                    builder.Append("</Run>");
                } else {
                    builder.Append(c);
                }
            }
            builder.Append(string.Format("<Run Foreground=\"Gray\">{0}</Run>", array[1]));
            string output = builder.ToString();
            
            string wrappedXml = string.Format("<TextBlock TextAlignment=\"Center\" xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" xml:space=\"preserve\" TextWrapping=\"Wrap\">{0}</TextBlock>", output);

            using (StringReader stringReader = new StringReader(wrappedXml)) {
                using (XmlReader xmlReader = XmlReader.Create(stringReader)) {
                    return XamlReader.Load(xmlReader);
                }
            }
        }

        /// <summary>
        /// Not implemented!
        /// </summary>
        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) {
            throw new NotImplementedException("The converter does not support two-way binding.");
        }
    }
}
