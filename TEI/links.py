import lxml.etree as ET
import os

# CONFIGURATION
MAIN_FILE = "issue_4-5.xml"  # Change this if your main file has a different name

def check_broken_links(filename):
    print(f"--- Scanning project starting from: {filename} ---")
    
    try:
        # 1. Parse the file and process XIncludes (merge all files into one memory object)
        parser = ET.XMLParser(resolve_entities=True)
        tree = ET.parse(filename, parser)
        tree.xinclude()  # This magically pulls in all your list_*.xml files
        root = tree.getroot()
        
    except Exception as e:
        print(f"CRITICAL ERROR: Could not parse or merge files. {e}")
        return

    # 2. Collect ALL IDs that exist in the entire project
    # We look for any element with an xml:id attribute
    all_ids = set()
    for elem in root.xpath('//*[@xml:id]'):
        all_ids.add(elem.attrib['{http://www.w3.org/XML/1998/namespace}id'])

    print(f"Found {len(all_ids)} unique IDs (people, places, works, etc.).")

    # 3. Collect ALL references (links)
    # We look for common linking attributes: ref, who, ana, target, ptr
    # You can add more to this list if you use custom ones.
    link_attributes = ['ref', 'who', 'ana', 'target']
    
    broken_links = []

    for elem in root.iter():
        for attr in link_attributes:
            if attr in elem.attrib:
                val = elem.attrib[attr]
                
                # Handle multiple values (e.g., ana="#theme1 #theme2")
                refs = val.split()
                
                for r in refs:
                    if r.startswith('#'):
                        clean_id = r[1:] # Remove the '#'
                        if clean_id not in all_ids:
                            # Record the error
                            line_num = elem.sourceline
                            broken_links.append(f"Line {line_num}: <{elem.tag}> points to '{r}', but ID '{clean_id}' does not exist.")

    # 4. Report Results
    if broken_links:
        print(f"\n❌ FOUND {len(broken_links)} BROKEN LINKS:\n")
        for error in broken_links:
            print(error)
    else:
        print("\n✅ SUCCESS! All links are valid.")

if __name__ == "__main__":
    check_broken_links(MAIN_FILE)