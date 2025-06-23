import pandas as pd
import ast
import os

def load_and_preprocess_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    # Define columns to drop for clarity and easier maintenance
    columns_to_drop = [
        'original_title', 'tagline', 'video', 'poster_path', 'status'
    ]
    df.drop(columns=columns_to_drop, inplace=True)

    # Define columns where NaN values are critical and should lead to row removal
    critical_columns_for_na = [
        'release_date', 'popularity', 'revenue', 'budget'
    ]
    df.dropna(subset=critical_columns_for_na, inplace=True)

    return df

def safe_literal_eval(value):
    if pd.isna(value):
        return []
    try:
        evaluated = ast.literal_eval(value)
        # Ensure the output is always a list for consistent processing
        return evaluated if isinstance(evaluated, list) else [evaluated]
    except (ValueError, SyntaxError):
        return []

def extract_nested_data(df: pd.DataFrame, column_name: str, id_key: str, name_key: str,
                        keys_to_remove: list = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_extracted_items = []
    expanded_rows = []

    for index, row in df.iterrows():
        # Use safe_literal_eval to handle various input formats and NaNs
        items = safe_literal_eval(row[column_name])

        for item in items:
            if isinstance(item, dict):
                # Clean the dictionary if keys_to_remove are specified
                if keys_to_remove:
                    item = {k: v for k, v in item.items() if k not in keys_to_remove}
                all_extracted_items.append(item)

                # Append to expanded_rows for the N:N relationship
                if id_key in item and name_key in item:
                    expanded_rows.append({
                        'movie_id': row['id'],
                        'movie_title': row['title'],
                        f'{id_key}_id': item[id_key],
                        f'{name_key}_name': item[name_key]
                    })

    # Create DataFrame of unique entities
    unique_entities_df = pd.DataFrame(all_extracted_items).drop_duplicates(subset=[id_key]).reset_index(drop=True)
    if 'name' not in unique_entities_df.columns and name_key in unique_entities_df.columns:
         unique_entities_df.rename(columns={name_key: 'name'}, inplace=True)


    # Create DataFrame for N:N relationship
    many_to_many_df = pd.DataFrame(expanded_rows)

    return unique_entities_df, many_to_many_df

def process_collections(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Using apply with safe_literal_eval and a lambda to get collection name
    def get_collection_name(x):
        collection_data = safe_literal_eval(x)
        if collection_data and isinstance(collection_data, list) and collection_data[0] and 'name' in collection_data[0]:
            return collection_data[0]['name']
        return None

    df['collection_name'] = df['belongs_to_collection'].apply(get_collection_name)

    # Extract unique collections for a separate table
    # This specifically handles the 'belongs_to_collection' where it's a single dict or None
    collection_items = [
        item[0] for item in df['belongs_to_collection'].apply(safe_literal_eval)
        if item and isinstance(item, list) and item[0] and isinstance(item[0], dict)
    ]
    collections_df = pd.DataFrame(collection_items).drop_duplicates(subset=['id']).reset_index(drop=True)
    # Remove specific keys if they exist in collections_df
    columns_to_remove = ['poster_path', 'backdrop_path']
    for col in columns_to_remove:
        if col in collections_df.columns:
            collections_df.drop(columns=col, inplace=True)

    return collections_df, df

def convert_numeric_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
    return df

def print_non_null_counts(df: pd.DataFrame, columns: list):
    print("\n--- Non-Null Value Counts ---")
    for col in columns:
        non_null_count = df[col].notna().sum()
        print(f"'{col}': {non_null_count} non-null rows")

def export_dataframes_to_csv(dataframes: dict, output_dir: str = 'output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"\n--- Exporting DataFrames to '{output_dir}/' ---")
    for name, df in dataframes.items():
        file_path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(file_path, index=False)
        print(f"Exported '{name}.csv' ({df.shape[0]} rows, {df.shape[1]} columns)")
    print("All DataFrames exported successfully.")

def main():
    # Configuration
    DATA_PATH = "files/movies_metadata.csv"

    # 1. Load and Initial Preprocessing
    print("Loading and initial preprocessing...")
    movies_df = load_and_preprocess_data(DATA_PATH)
    print("Initial preprocessing complete.")
    print("-" * 50)

    # 2. Process Collections
    print("Processing collections...")
    collections_df, movies_df = process_collections(movies_df.copy()) # Use a copy to avoid SettingWithCopyWarning
    print(f"Collections DataFrame created. Shape: {collections_df.shape}")
    print(f"Main DataFrame with 'collection_name' updated. Shape: {movies_df.shape}")
    print("-" * 50)

    # 3. Process Genres
    print("Processing genres...")
    genres_df, genres_movies_df = extract_nested_data(movies_df, "genres", "id", "name")
    print(f"Genres DataFrame created. Shape: {genres_df.shape}")
    print(f"Genres-Movies N:N DataFrame created. Shape: {genres_movies_df.shape}")
    print("-" * 50)

    # 4. Process Production Companies
    print("Processing production companies...")
    prod_companies_df, prod_companies_movies_df = extract_nested_data(
        movies_df, "production_companies", "id", "name"
    )
    print(f"Production Companies DataFrame created. Shape: {prod_companies_df.shape}")
    print(f"Production Companies-Movies N:N DataFrame created. Shape: {prod_companies_movies_df.shape}")
    print("-" * 50)

    # 5. Process Production Countries
    print("Processing production countries...")
    countries_df, countries_movies_df = extract_nested_data(
        movies_df, "production_countries", "iso_3166_1", "name"
    )
    # Rename id column for consistency
    if 'iso_3166_1' in countries_df.columns:
        countries_df.rename(columns={'iso_3166_1': 'id'}, inplace=True)
    print(f"Countries DataFrame created. Shape: {countries_df.shape}")
    print(f"Countries-Movies N:N DataFrame created. Shape: {countries_movies_df.shape}")
    print("-" * 50)

    # 6. Process Spoken Languages
    print("Processing spoken languages...")
    spoken_languages_df, spoken_languages_movies_df = extract_nested_data(
        movies_df, "spoken_languages", "iso_639_1", "name"
    )
    # Rename id column for consistency
    if 'iso_639_1' in spoken_languages_df.columns:
        spoken_languages_df.rename(columns={'iso_639_1': 'id'}, inplace=True)
    print(f"Spoken Languages DataFrame created. Shape: {spoken_languages_df.shape}")
    print(f"Spoken Languages-Movies N:N DataFrame created. Shape: {spoken_languages_movies_df.shape}")
    print("-" * 50)

    # 7. Convert Numeric Columns
    print("Converting numeric columns...")
    numeric_cols = ['budget', 'revenue', 'runtime']
    movies_df = convert_numeric_columns(movies_df, numeric_cols)
    print("Numeric column conversion complete.")
    print("-" * 50)

    # 8. Print Non-Null Counts
    print_non_null_counts(movies_df, ['budget', 'revenue', 'runtime', 'overview'])

    # Display a sample of the main DataFrame
    print("\n--- Sample of Preprocessed Movies DataFrame ---")
    print(movies_df.head())

    # Criar um dicionário com todos os DataFrames a serem exportados
    dataframes_to_export = {
        'movies': movies_df,
        'collections': collections_df,
        'genres': genres_df,
        'genres_movies': genres_movies_df,
        'production_companies': prod_companies_df,
        'production_companies_movies': prod_companies_movies_df,
        'countries': countries_df,
        'countries_movies': countries_movies_df,
        'spoken_languages': spoken_languages_df,
        'spoken_languages_movies': spoken_languages_movies_df
    }

    OUTPUT_DIR = "files/processed_data" 
    # Chamar a função de exportação
    export_dataframes_to_csv(dataframes_to_export, OUTPUT_DIR)

    print("\n--- DataFrames Export Complete ---")
    print(f"Os arquivos CSV foram salvos em: '{os.path.abspath(OUTPUT_DIR)}'")

main()