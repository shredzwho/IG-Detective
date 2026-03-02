class Endpoints:
    BASE_URL = "https://www.instagram.com"
    GRAPHQL_URL = "https://www.instagram.com/graphql/query/"
    I_API_BASE = "https://i.instagram.com/api/v1"
    
    # Login & Auth
    LOGIN = f"{BASE_URL}/accounts/login/ajax/"
    TWO_FACTOR_LOGIN = f"{BASE_URL}/accounts/login/ajax/two_factor/"
    
    # Search & Discovery
    WEB_PROFILE_INFO = f"{I_API_BASE}/users/web_profile_info/?username={{username}}"
    
    # GraphQL Query Hashes (These change occasionally but are stable for long periods)
    # Finding these hashes typically involves inspecting network traffic on IG Web.
    HASH_POSTS = "blindingly_hardcoded_or_extracted_dynamically" # Placeholders for actual implementations
    HASH_FOLLOWERS = "c76146de99bb02f641520449d8654661"
    HASH_FOLLOWINGS = "d04b0a864b4b54837c0d870b0e77e076"
    HASH_COMMENTS = "bc3296d1ce80a24b1b6e40b1e72903f5"
    @staticmethod
    def user_info(username: str) -> str:
        return f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
    @staticmethod
    def media_info(shortcode: str) -> str:
        return f"https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables={{\"shortcode\":\"{shortcode}\"}}"
    
    @staticmethod
    def followers(user_id: str, count: int, end_cursor: str = "") -> str:
        var = f'{{"id":"{user_id}","include_reel":true,"fetch_mutual":false,"first":{count},"after":"{end_cursor}"}}'
        import urllib.parse
        return f"{Endpoints.GRAPHQL_URL}?query_hash={Endpoints.HASH_FOLLOWERS}&variables={urllib.parse.quote(var)}"

    @staticmethod
    def followings(user_id: str, count: int, end_cursor: str = "") -> str:
        var = f'{{"id":"{user_id}","includes_hashtags":true,"search_surface":"follow_list_page","first":{count},"after":"{end_cursor}"}}'
        import urllib.parse
        return f"{Endpoints.GRAPHQL_URL}?query_hash={Endpoints.HASH_FOLLOWINGS}&variables={urllib.parse.quote(var)}"
