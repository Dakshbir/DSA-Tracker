import httpx
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

# Import the web scraper
try:
    from leetcode_scraper import leetcode_scraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    print("⚠️  Selenium/WebDriver not available. Web scraping will be disabled.")


class PlatformService:
    """
    Enhanced service to fetch data from LeetCode and Codeforces.
    
    Improvements:
    - Fixed LeetCode GraphQL query
    - Fetches difficulty for each LeetCode problem
    - Returns actual Codeforces ratings instead of difficulty labels
    - Handles API rate limits
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)  # Increased timeout
    
    async def close(self):
        await self.client.aclose()
    
    # ============= LEETCODE - FIXED =============
    
    async def fetch_leetcode_stats(self, username: str) -> Dict:
        """
        Fetch LeetCode user statistics.
        Fixed GraphQL query format.
        """
        url = "https://leetcode.com/graphql"
        
        # Simplified and fixed query
        query = """
        query userPublicProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """
        
        try:
            response = await self.client.post(
                url,
                json={
                    "query": query,
                    "variables": {"username": username},
                    "operationName": "userPublicProfile"
                },
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://leetcode.com"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"LeetCode API error: {data['errors'][0].get('message', 'Unknown error')}")
            
            matched_user = data.get("data", {}).get("matchedUser")
            
            if not matched_user:
                raise Exception(f"User '{username}' not found on LeetCode")
            
            ac_submissions = matched_user["submitStatsGlobal"]["acSubmissionNum"]
            
            stats = {
                "username": username,
                "platform": "leetcode",
                "total_solved": 0,
                "easy_solved": 0,
                "medium_solved": 0,
                "hard_solved": 0
            }
            
            for item in ac_submissions:
                difficulty = item["difficulty"]
                count = item["count"]
                
                if difficulty == "All":
                    stats["total_solved"] = count
                elif difficulty == "Easy":
                    stats["easy_solved"] = count
                elif difficulty == "Medium":
                    stats["medium_solved"] = count
                elif difficulty == "Hard":
                    stats["hard_solved"] = count
            
            return stats
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"LeetCode API returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Error fetching LeetCode stats: {str(e)}")
    
    async def fetch_leetcode_recent_submissions(
        self, 
        username: str, 
        limit: int = 500,
        use_scraper: bool = True,
        email: str = None,
        password: str = None
    ) -> List[Dict]:
        """
        Fetch LeetCode submissions with difficulty.
        
        Fetches from public API (latest 20 most recent submissions).
        
        Args:
            username: LeetCode username
            limit: Maximum submissions to fetch
            use_scraper: Deprecated - kept for API compatibility
            email: Deprecated - kept for API compatibility
            password: Deprecated - kept for API compatibility
        """
        url = "https://leetcode.com/graphql"
        
        try:
            all_submissions = []
            
            print(f"📥 Fetching LeetCode submissions for {username}...")
            print(f"   Using public API (limited to 20 most recent submissions)...")
            all_submissions = await self._fetch_leetcode_public_api(username)
            
            print(f"📥 Total accepted submissions: {len(all_submissions)}")
            
            if not all_submissions:
                raise Exception(f"No submissions found for user {username}")
            
            # Fetch difficulty for each unique problem
            enhanced_submissions = []
            seen_slugs = set()
            
            print(f"📥 Fetching difficulty for {len(all_submissions)} problems...")
            
            for i, sub in enumerate(all_submissions):
                slug = sub.get("titleSlug")
                
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                
                # Fetch difficulty
                difficulty = sub.get("difficulty", "Unknown")
                if difficulty == "Unknown":
                    difficulty = await self.fetch_leetcode_problem_difficulty(slug)
                
                enhanced_submissions.append({
                    "title": sub.get("title", "Unknown"),
                    "question_id": slug,
                    "difficulty": difficulty,
                    "solved_date": datetime.fromtimestamp(int(sub.get("timestamp", 0))),
                    "platform": "leetcode"
                })
                
                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{len(all_submissions)} problems...")
                
                await asyncio.sleep(0.1)
            
            print(f"✅ Fetched {len(enhanced_submissions)} problems from LeetCode")
            
            if len(enhanced_submissions) > 20:
                print(f"📌 Success! Got {len(enhanced_submissions)} problems (much better than API limit of 20)")
            
            return enhanced_submissions
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise Exception(f"Error fetching LeetCode submissions: {str(e)}")
    
    async def _fetch_leetcode_public_api(self, username: str) -> List[Dict]:
        """
        Fallback: Fetch using public GraphQL API (limited to 20 most recent)
        """
        url = "https://leetcode.com/graphql"
        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
            recentAcSubmissionList(username: $username, limit: $limit) {
                title
                titleSlug
                timestamp
            }
        }
        """
        
        try:
            response = await self.client.post(
                url,
                json={"query": query, "variables": {"username": username, "limit": 20}},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://leetcode.com"
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_msg = data['errors'][0].get('message', str(data['errors'])) if data['errors'] else 'Unknown error'
                print(f"❌ GraphQL Error: {error_msg}")
                raise Exception(f"LeetCode API error: {error_msg}")
            
            all_submissions = data.get("data", {}).get("recentAcSubmissionList", [])
            print(f"   ✓ Retrieved {len(all_submissions)} most recent submissions from public API")
            
            return all_submissions
            
        except Exception as e:
            print(f"❌ Public API Error: {str(e)}")
            return []
    
    async def fetch_leetcode_problem_difficulty(self, title_slug: str) -> str:
        """
        Fetch difficulty for a specific LeetCode problem.
        """
        url = "https://leetcode.com/graphql"
        
        query = """
        query getQuestionDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                difficulty
            }
        }
        """
        
        try:
            response = await self.client.post(
                url,
                json={
                    "query": query,
                    "variables": {"titleSlug": title_slug},
                    "operationName": "getQuestionDetail"
                },
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://leetcode.com"
                }
            )
            
            data = response.json()
            question = data.get("data", {}).get("question", {})
            return question.get("difficulty", "Unknown")
            
        except Exception as e:
            print(f"⚠️  Could not fetch difficulty for {title_slug}: {e}")
            return "Unknown"
    
    # ============= CODEFORCES - ENHANCED =============
    
    async def fetch_codeforces_stats(self, username: str) -> Dict:
        """
        Fetch Codeforces user statistics.
        """
        url = f"https://codeforces.com/api/user.info?handles={username}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                raise Exception(f"Codeforces API error: {data.get('comment', 'Unknown error')}")
            
            user_data = data["result"][0]
            
            stats = {
                "username": username,
                "platform": "codeforces",
                "rating": user_data.get("rating", 0),
                "max_rating": user_data.get("maxRating", 0),
                "rank": user_data.get("rank", "unrated"),
                "max_rank": user_data.get("maxRank", "unrated")
            }
            
            return stats
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch Codeforces data: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing Codeforces data: {str(e)}")
    
    async def fetch_codeforces_submissions(
        self, 
        username: str, 
        limit: int = 100000  # Fetch ALL submissions (up to 100k)
    ) -> List[Dict]:
        """
        Fetch ALL Codeforces submissions with ACTUAL ratings (not difficulty labels).
        
        Returns problems with their actual rating (e.g., 800, 1200, 1600)
        instead of Easy/Medium/Hard labels.
        
        Uses pagination to fetch all submissions until no more are available.
        Continues fetching until:
        1. API returns fewer submissions than requested (reached end)
        2. OR reaches the limit (100k submissions)
        """
        try:
            all_submissions = []
            page_size = 500  # Codeforces API returns max 500 per request
            from_index = 1
            total_fetched = 0
            
            print(f"📥 Fetching ALL Codeforces submissions for {username}...")
            print(f"   This may take a moment for users with many submissions...")
            
            while total_fetched < limit:
                url = f"https://codeforces.com/api/user.status?handle={username}&from={from_index}&count={page_size}"
                
                print(f"   Fetching batch starting at index {from_index}...")
                
                try:
                    response = await self.client.get(url, timeout=30.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data["status"] != "OK":
                        error_msg = data.get('comment', 'Unknown error')
                        print(f"⚠️  API Error: {error_msg}")
                        raise Exception(f"Codeforces API error: {error_msg}")
                    
                    submissions = data["result"]
                    
                    if not submissions:
                        print(f"   ✓ Reached end of submissions (no more data)")
                        break  # No more submissions
                    
                    all_submissions.extend(submissions)
                    total_fetched += len(submissions)
                    print(f"   ✓ Got {len(submissions)} submissions. Total so far: {total_fetched}")
                    
                    # If we got fewer than page_size, we've reached the end
                    if len(submissions) < page_size:
                        print(f"   ✓ Reached end of submissions")
                        break
                    
                    # Move to next batch
                    from_index += page_size
                    
                    # Add delay between requests to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except httpx.HTTPStatusError as e:
                    print(f"❌ HTTP Error {e.response.status_code}")
                    break
                except Exception as e:
                    print(f"❌ Error at index {from_index}: {str(e)}")
                    break
            
            print(f"📥 Total submissions fetched from API: {len(all_submissions)}")
            
            # Filter accepted submissions
            accepted = []
            seen_problems = set()
            
            for sub in all_submissions:
                # Only count accepted solutions
                if sub.get("verdict") != "OK":
                    continue
                
                problem = sub["problem"]
                problem_id = f"{problem['contestId']}{problem['index']}"
                
                # Skip duplicates
                if problem_id in seen_problems:
                    continue
                seen_problems.add(problem_id)
                
                # Get actual rating (this is the problem's difficulty rating)
                rating = problem.get("rating", None)
                
                # Get tags
                tags = problem.get("tags", [])
                topic_str = ", ".join(tags) if tags else None
                
                accepted.append({
                    "title": problem["name"],
                    "question_id": problem_id,
                    "difficulty": str(rating) if rating else "Unrated",  # Store as string: "1200", "1500", etc.
                    "topic": topic_str,
                    "solved_date": datetime.fromtimestamp(sub["creationTimeSeconds"]),
                    "platform": "codeforces"
                })
            
            print(f"✅ Found {len(accepted)} unique accepted Codeforces problems out of {len(all_submissions)} total")
            return accepted
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise Exception(f"Error fetching Codeforces submissions: {str(e)}")


# Global instance
platform_service = PlatformService()    