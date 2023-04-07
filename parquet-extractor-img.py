import pyarrow.parquet as pq
import pandas as pd
import re

def parse_column_selection(selection, headers):
    columns = []
    parts = selection.split(',')

    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            columns.extend(headers[start - 1:end])
        else:
            index = int(part) - 1
            columns.append(headers[index])

    return columns

def filter_image_urls(value):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    pattern = r'https?:\/\/[^\'"]*(' + '|'.join(image_extensions) + ')'

    if isinstance(value, bytes):
        value = value.decode('utf-8')

    match = re.search(pattern, value)
    return match.group(0) if match else None

def deduplicate_urls(image_urls):
    unique_urls = list(set(image_urls))
    return unique_urls

def main():
    # Read the Parquet file and display column headers
    parquet_file = 'compressed.parquet'
    table = pq.read_table(parquet_file)
    headers = table.schema.names

    print("Column headers:")
    for i, header in enumerate(headers, start=1):
        print(f"{i}. {header}")

    # Prompt the user to select columns
    selected_columns_str = input("Enter the column numbers you want to extract (e.g., '1, 2, 3' or '1-3'): ")
    selected_columns = parse_column_selection(selected_columns_str, headers)

    # Check if the selected columns exist
    if all(column in headers for column in selected_columns):
        # Select the desired columns and convert them to a Pandas DataFrame
        selected_table = table.select(selected_columns)
        df = selected_table.to_pandas()

        # Filter out only image URLs
        for column in selected_columns:
            df[column] = df[column].apply(filter_image_urls)
        
        # Remove rows with no image URLs
        df.dropna(how='all', subset=selected_columns, inplace=True)

        # Collect image URLs and deduplicate them
        image_urls = []
        for index, row in df.iterrows():
            for column in selected_columns:
                if row[column]:
                    image_urls.append(row[column])
        unique_urls = deduplicate_urls(image_urls)

        # Save the unique image URLs to a text file
        output_txt = 'myimglist.txt'
        with open(output_txt, 'w') as f:
            for url in unique_urls:
                f.write(f"{url}\n")

        print(f"Image URLs from the selected columns have been saved to '{output_txt}'.")
    else:
        print("Error: One or more selected columns not found.")

if __name__ == '__main__':
    main()
