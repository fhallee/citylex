import argparse
import csv
import io
import sqlite3

from citylex import features
from flask import Flask, render_template, request, send_file

def get_args():
    parser = argparse.ArgumentParser(description="Run the Flask app with a specified database path.")
    parser.add_argument(
        "--db_path",
        default="data/citylex.db",
        help="Path to the database file (default: %(default)s)"
    )
    return parser.parse_args()

args = get_args()
db_path = args.db_path

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if request.method == "GET":
        return render_template('index.html')
    elif request.method == "POST":
        selected_sources = request.form.getlist("sources[]")
        selected_fields = request.form.getlist("fields[]")
        output_format = request.form["output_format"]
        licenses = request.form.getlist("licenses")
        if not selected_sources or not selected_fields:
            return "Please select at least one data source and field.", 400
        print(selected_sources)
        print(selected_fields)
        print(output_format)
        print(licenses)

        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')

        columns = ["wordform", "source"]
        if "subtlexus_raw_frequency" in selected_fields or "subtlexuk_raw_frequency" in selected_fields:
            columns.append("raw_frequency")
        if "subtlexus_freq_per_million" in selected_fields or "subtlexuk_freq_per_million" in selected_fields:
            columns.append("freq_per_million")
        if "wikipronus_IPA" in selected_fields or "wikipronuk_IPA" in selected_fields:
            columns.append("IPA_pronunciation")
        if "udlex_CELEXtags" in selected_fields or "um_CELEXtags" in selected_fields:
            columns.append("CELEX_tags")
        if "udlex_UDtags" in selected_fields or "um_UDtags" in selected_fields:
            columns.append("UD_tags")
        if "udlex_UMtags" in selected_fields or "um_UMtags" in selected_fields:
            columns.append("UniMorph_tags")

        writer.writerow(columns)  # Write header

        # Fetch and write SUBTLEX-US data
        if "SUBTLEX-US" in selected_sources:
            us_columns = ["wordform", "source"]
            if "subtlexus_raw_frequency" in selected_fields:
                us_columns.append("raw_frequency")
            if "subtlexus_freq_per_million" in selected_fields:
                us_columns.append("freq_per_million")
            us_query = f"SELECT {', '.join(us_columns)} FROM frequency WHERE source = 'SUBTLEX-US'"
            cursor.execute(us_query)
            us_results = cursor.fetchall()
            for row in us_results:
                row_dict = dict(zip(us_columns, row))
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write US data

        # Fetch and write SUBTLEX-UK data
        if "SUBTLEX-UK" in selected_sources:
            uk_columns = ["wordform", "source"]
            if "subtlexuk_raw_frequency" in selected_fields:
                uk_columns.append("raw_frequency")
            if "subtlexuk_freq_per_million" in selected_fields:
                uk_columns.append("freq_per_million")
            uk_query = f"SELECT {', '.join(uk_columns)} FROM frequency WHERE source = 'SUBTLEX-UK'"
            cursor.execute(uk_query)
            uk_results = cursor.fetchall()
            for row in uk_results:
                row_dict = dict(zip(uk_columns, row))
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write UK data

        # Fetch and write WikiPron-US data
        if "WikiPron-US" in selected_sources:
            wp_us_columns = ["wordform", "source", "pronunciation"]
            wp_us_query = f"SELECT wordform, source, pronunciation FROM pronunciation WHERE source = 'WikiPron US' AND standard = 'IPA'"
            cursor.execute(wp_us_query)
            wp_us_results = cursor.fetchall()
            for row in wp_us_results:
                row_dict = dict(zip(wp_us_columns, row))
                row_dict["IPA_pronunciation"] = row_dict.pop("pronunciation")
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write WikiPron-US data

        # Fetch and write WikiPron-UK data
        if "WikiPron-UK" in selected_sources:
            wp_uk_columns = ["wordform", "source", "pronunciation"]
            wp_uk_query = f"SELECT wordform, source, pronunciation FROM pronunciation WHERE source = 'WikiPron UK' AND standard = 'IPA'"
            cursor.execute(wp_uk_query)
            wp_uk_results = cursor.fetchall()
            for row in wp_uk_results:
                row_dict = dict(zip(wp_uk_columns, row))
                row_dict["IPA_pronunciation"] = row_dict.pop("pronunciation")
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write WikiPron-UK data

            # Fetch and write UDLexicons data
        if "UDLexicons" in selected_sources:
            udlex_columns = ["wordform", "source", "features"]
            udlex_query = f"SELECT wordform, source, features FROM features WHERE source = 'UDLexicons'"
            cursor.execute(udlex_query)
            udlex_results = cursor.fetchall()
            for row in udlex_results:
                row_dict = dict(zip(udlex_columns, row))
                combined_tag = '|'.join(row_dict["features"].split('|'))
                if "udlex_CELEXtags" in selected_fields:
                    row_dict["CELEX_tags"] = features.tag_to_tag("UD", "CELEX", combined_tag)
                if "udlex_UDtags" in selected_fields:
                    row_dict["UD_tags"] = combined_tag
                if "udlex_UMtags" in selected_fields:
                    row_dict["UniMorph_tags"] = features.tag_to_tag("UD", "UniMorph", combined_tag)
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write UDLexicons data

        # Fetch and write UniMorph data
        if "UniMorph" in selected_sources:
            um_columns = ["wordform", "source", "features"]
            um_query = f"SELECT wordform, source, features FROM features WHERE source = 'UniMorph'"
            cursor.execute(um_query)
            um_results = cursor.fetchall()
            for row in um_results:
                row_dict = dict(zip(um_columns, row))
                combined_tag = '|'.join(row_dict["features"].split('|'))
                if "um_CELEXtags" in selected_fields:
                    row_dict["CELEX_tags"] = features.tag_to_tag("UniMorph", "CELEX", combined_tag)
                if "um_UDtags" in selected_fields:
                    row_dict["UD_tags"] = features.tag_to_tag("UniMorph", "UD", combined_tag)
                if "um_UMtags" in selected_fields:
                    row_dict["UniMorph_tags"] = combined_tag
                writer.writerow([row_dict.get(col, '') for col in columns])  # Write UniMorph data

        output.seek(0)  # Move the cursor to the beginning of the file

        # Send the file as a response
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/tab-separated-values',
            as_attachment=True,
            download_name='citylex_data.tsv'
            )


if __name__ == "__main__":
    app.run()