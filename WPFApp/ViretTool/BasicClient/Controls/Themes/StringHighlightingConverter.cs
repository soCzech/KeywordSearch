// inspired by: http://underground.infovark.com/2011/03/03/highlighting-query-terms-in-a-wpf-textblock/

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

namespace ViretTool.BasicClient.Controls {

    /// <summary>
    /// Converts string to WPF TextBlock with parts of text in red.
    /// </summary>
    [ValueConversion(typeof(string), typeof(object))]
    public sealed class StringHighlightingConverter : IValueConverter {
        public const string HIGHLIGHT_START_TAG = "$~START~$";
        public const string HIGHLIGHT_END_TAG = "$~END~$";

        /// <summary>
        /// Takes string and makes text between <see cref="HIGHLIGHT_START_TAG"/> and <see cref="HIGHLIGHT_END_TAG"/> red
        /// </summary>
        /// <param name="value">String to be converted</param>
        /// <param name="targetType">Not used</param>
        /// <param name="parameter">Not used</param>
        /// <param name="culture">Not used</param>
        /// <returns>WPF TextBlock with parts of text in red</returns>
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture) {
            string input = value as string;
            if (input == null) return null;

            string escaped = SecurityElement.Escape(input);
            // solves errors 'Dynamic resource not found'
            // string xml = escaped.Replace(START_TAG, "<Run Style=\"{DynamicResource ResourceKey=HighlightedText}\">").Replace(END_TAG, "</Run>");
            string xml = escaped.Replace(HIGHLIGHT_START_TAG, "<Run Foreground=\"Red\">").Replace(HIGHLIGHT_END_TAG, "</Run>");

            string wrappedXml = string.Format("<TextBlock xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" xml:space=\"preserve\" TextWrapping=\"Wrap\">{0}</TextBlock>", xml);

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
