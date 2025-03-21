import whois
import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def whois_lookup(domain: str) -> str:
    try:
        domain_info = whois.whois(domain)
        if domain_info:
            info_parts = [
                f"Domain Name: {domain_info.domain_name}",
                f"Registrar: {domain_info.registrar}",
                f"Creation Date: {domain_info.creation_date}",
                f"Expiration Date: {domain_info.expiration_date}",
                f"Name Servers: {domain_info.name_servers}"
            ]
            # Add more details if available
            if hasattr(domain_info, 'emails') and domain_info.emails:
                info_parts.append(f"Contact Emails: {domain_info.emails}")
            if hasattr(domain_info, 'status') and domain_info.status:
                info_parts.append(f"Status: {domain_info.status}")
            return "\n".join(info_parts)
        else:
            return "No WHOIS information found."
    except whois.parser.PywhoisError as e:
        logging.error(f"WHOIS lookup failed for domain {domain}: {e}")
        return f"Error fetching domain info: {e}"
    except Exception as e:
        logging.error(f"Unexpected error during WHOIS lookup for domain {domain}: {e}")
        return f"Error fetching domain info: {e}"

def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from a given text using regex.
    """
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text)
    return list(set(emails))  # Remove duplicates

def filter_emails_by_domain(emails: List[str], domain: str) -> List[str]:
    """
    Filter a list of emails to only include those ending with the specified domain.
    """
    domain = domain.lower()
    return [email for email in emails if email.lower().endswith("@" + domain)]

def basic_web_scraping(email: str) -> str:
    # Prepare the search URL for the provided email
    url = f"https://www.google.com/search?q={email}+breach"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get top 5 search result titles
        search_results = soup.find_all('h3')
        titles = [result.text for result in search_results[:5]]

        # Extract emails from the page text
        page_text = soup.get_text()
        found_emails = extract_emails(page_text)
        # Filter emails based on the domain from the provided email address
        user_domain = email.split('@')[-1]
        filtered_emails = filter_emails_by_domain(found_emails, user_domain)

        result_message = f"Top search results for '{email}':\n" + "\n".join(titles) if titles else f"No search results found for '{email}'."
        if filtered_emails:
            result_message += "\n\nDetected Email Addresses matching domain:\n" + "\n".join(filtered_emails)
        else:
            result_message += "\n\nNo email addresses detected matching the domain."
        
        return result_message
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred while fetching search results for {email}: {e}")
        return f"Failed to retrieve search results. HTTP error: {e}"
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception occurred while fetching search results for {email}: {e}")
        return f"Error fetching search results: {e}"
    except Exception as e:
        logging.error(f"Unexpected error during web scraping for {email}: {e}")
        return f"Error fetching search results: {e}"

# Example usage:
if __name__ == "__main__":
    # WHOIS lookup example
    domain = "example.com"
    logging.info("Performing WHOIS lookup...")
    print(whois_lookup(domain))
    
    # Basic web scraping example with email detection and filtering by domain
    email_query = "test@example.com"
    logging.info("Performing basic web scraping with email detection...")
    print(basic_web_scraping(email_query))
