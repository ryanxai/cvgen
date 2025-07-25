#!/usr/bin/env python3
import json
import re
import os
import subprocess
import sys
from datetime import datetime

# Define output directory (will be used in Docker)
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '.')

def load_resume_data(file_path='resume.json'):
    """Load JSON data from resume.json file"""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON content in {file_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} not found")

def escape_latex(text):
    """Escape special LaTeX characters in text"""
    if text is None:
        return ""
    
    # Handle special case for ampersands - check if they're already escaped
    text = text.replace('&', '\\&')
    text = text.replace('\\\\&', '\\&')  # Fix double-escaping
    
    # First handle backslash to avoid issues with other replacements
    # Skip this step since we've already handled ampersands
    # text = text.replace('\\', '\\textbackslash{}')
    
    # Define replacements for special LaTeX characters
    replacements = {
        # '&': '\\&',  # Already handled above
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
    }
    
    # Apply replacements
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def format_contact_links(links):
    """Format contact links for LaTeX"""
    if not links:
        return ""
    
    links_latex = []
    for link in links:
        # Skip links that don't have both name and url, or if they're empty
        if not link.get('name') or not link.get('url') or not link['name'].strip() or not link['url'].strip():
            continue
        
        name = escape_latex(link['name'].strip())
        url = link['url'].strip()
        links_latex.append(f"\\href{{{url}}}{{{name}}}")
    
    return " $\\vert$ ".join(links_latex)

def format_skills(skills):
    """Format skills section for LaTeX"""
    if not skills:
        return ""
    
    skills_latex = []
    for skill in skills:
        # Ensure ampersands are properly escaped - direct replacement
        category = skill['category'].replace('&', '\\&')
        
        # Handle items as a list and join with commas
        if isinstance(skill['items'], list):
            items_list = skill['items']
        else:
            # Fallback for backward compatibility - treat as string and split
            items_list = skill['items'].split(', ') if isinstance(skill['items'], str) else [skill['items']]
        
        # Skip if no items
        if not items_list:
            continue
        
        # Join items with commas and escape
        items_text = ', '.join(items_list)
        items_text = items_text.replace('&', '\\&')
        
        # Then apply general escaping for other special characters
        category = escape_latex(category)
        items_text = escape_latex(items_text)
        
        # Double check ampersands are properly escaped (in case escape_latex modified them)
        category = category.replace('\\\\&', '\\&')
        items_text = items_text.replace('\\\\&', '\\&')
        
        skills_latex.append(
            f"  \\resumeSubheading\n"
            f"    {{{category}}}{{}}\n"
            f"    {{{items_text}}}{{}}\n"
        )
    return "".join(skills_latex)

def format_experience(experience_items):
    """Format experience section for LaTeX"""
    if not experience_items:
        return ""
    
    experience_latex = []
    for exp in experience_items:
        # Skip if essential fields are empty
        if not exp.get("title") or not exp.get("company"):
            continue
            
        # Escape and prepare title and location
        title = escape_latex(exp["title"])
        location = escape_latex(exp["location"])
        company = escape_latex(exp["company"])
        
        # Prepare company with description if available
        if "company_description" in exp and exp["company_description"]:
            if "company_url" in exp and exp["company_url"]:
                company_desc = escape_latex(exp["company_description"])
                company_text = f"\\href{{{exp['company_url']}}}{{{company}}}{{: {company_desc}}}"
            else:
                company_desc = escape_latex(exp["company_description"])
                company_text = f"{company}{{: {company_desc}}}"
        else:
            if "company_url" in exp and exp["company_url"]:
                company_text = f"\\href{{{exp['company_url']}}}{{{company}}}"
            else:
                company_text = f"{company}"
        
        date_text = f"{exp['date_start']} - {exp['date_end']}"
        
        experience_latex.append(
            f"  \\resumeSubheading\n"
            f"  {{{title}}}{{{date_text}}}\n"
            f"  {{{company_text}}}{{{location}}}\n"
        )
        
        # Add achievements if available
        if "achievements" in exp and exp["achievements"]:
            experience_latex.append("    \\resumeItemListStart\n")
            for achievement in exp["achievements"]:
                name = escape_latex(achievement["name"])
                
                # Handle the description including any URLs more carefully
                description = achievement["description"]
                
                # First convert markdown links to LaTeX \href
                # Example: [text](url) to \href{url}{text}
                description = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\href{\2}{\1}', description)
                
                # Remove any double backslashes in URLs (especially before &)
                description = re.sub(r'\\href\{([^}]*?)\\&([^}]*?)\}', r'\\href{\1&\2}', description)
                
                # Now escape special LaTeX characters, but preserve the href commands
                # First temporarily replace href commands to protect them
                href_matches = re.findall(r'\\href\{[^}]*\}\{[^}]*\}', description)
                for i, match in enumerate(href_matches):
                    description = description.replace(match, f"HREFPLACEHOLDER{i}")
                
                # Escape LaTeX special characters
                description = escape_latex(description)
                
                # Put the href commands back
                for i, match in enumerate(href_matches):
                    description = description.replace(f"HREFPLACEHOLDER{i}", match)
                
                experience_latex.append(
                    f"      \\resumeItem{{{name}}}\n"
                    f"      {{{description}}}\n"
                )
            experience_latex.append("      \\resumeItemListEnd\n\n")
    
    return "".join(experience_latex)

def format_education(education_items):
    """Format education section for LaTeX"""
    if not education_items:
        return ""
    
    education_latex = []
    for edu in education_items:
        # Skip if essential fields are empty
        if not edu.get('degree') or not edu.get('institution'):
            continue
            
        degree = escape_latex(edu['degree'])
        institution = escape_latex(edu['institution'])
        location = escape_latex(edu['location'])
        
        education_latex.append(
            f"    \\resumeSubheading\n"
            f"      {{{degree}}}{{{edu['date_start']} -- {edu['date_end']}}}\n"
            f"      {{{institution}}}{{{location}}}\n"
        )
    return "".join(education_latex)

def format_awards(awards_items):
    """Format awards section for LaTeX"""
    if not awards_items:
        return ""
    
    awards_latex = []
    for award in awards_items:
        # Skip if essential fields are empty
        if not award.get("title") or not award.get("organization"):
            continue
            
        title = escape_latex(award["title"])
        organization = escape_latex(award["organization"])
        location = escape_latex(award["location"])
        
        organization_text = organization
        if "organization_detail" in award and award["organization_detail"]:
            org_detail = escape_latex(award["organization_detail"])
            if "organization_url" in award and award["organization_url"]:
                organization_text = f"{organization} $\\vert$ \\href{{{award['organization_url']}}}{{{org_detail.split(':')[-1].strip()}}}"
            else:
                organization_text = f"{organization} $\\vert$ {org_detail}"
        
        awards_latex.append(
            f"    \\resumeSubheading\n"
            f"      {{{title}}}{{{award['date']}}}\n"
            f"      {{{organization_text}}}{{{location}}}\n"
        )
    return "".join(awards_latex)

def format_certifications(cert_items):
    """Format certifications section for LaTeX"""
    if not cert_items:
        return ""
    
    cert_latex = []
    for cert in cert_items:
        # Skip if essential fields are empty
        if not cert.get("title") or not cert.get("organization"):
            continue
            
        title = escape_latex(cert["title"])
        organization = escape_latex(cert["organization"])
        
        cert_latex.append(
            f"    \\resumeSubheading\n"
            f"      {{{title}}}{{{cert['date']}}}\n"
            f"      {{\\href{{{cert['url']}}}{{Certificate}}}}{{{organization}}}\n"
        )
    return "".join(cert_latex)

def format_publications(pub_items):
    """Format publications section for LaTeX"""
    if not pub_items:
        return ""
    
    pub_latex = []
    for pub in pub_items:
        # Skip if essential fields are empty
        if not pub.get("authors") or not pub.get("title"):
            continue
            
        # Make the author's name bold if it appears in the authors list
        authors = escape_latex(pub["authors"]).replace("M. Ghorbandoost", "\\textbf{M. Ghorbandoost}")
        title = escape_latex(pub["title"])
        venue = escape_latex(pub["venue"])
        
        pub_latex.append(
            f"  \\item{{{authors}, ``{title}'', {venue}, {pub['year']}. \\href{{{pub['url']}}}{{link}}}}\n"
        )
        if pub != pub_items[-1]:  # Add spacing between items except the last one
            pub_latex.append("  \\vspace{5pt}\n")
    
    return "".join(pub_latex)

def generate_latex_resume(data, template_path='template.tex', output_path=None):
    """Generate a LaTeX resume from the template and data"""
    # Always use 'resume.tex' as the output filename
    default_output_name = 'resume.tex'
    
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, default_output_name)
        
    with open(template_path, 'r') as file:
        template = file.read()
    
    # Format the contact links
    contact_links = format_contact_links(data["contact"]["links"])
    
    # Format all sections
    skills_content = format_skills(data["skills"])
    experience_content = format_experience(data["experience"])
    education_content = format_education(data["education"])
    awards_content = format_awards(data["awards"])
    certifications_content = format_certifications(data["certifications"])
    publications_content = format_publications(data["publications"])
    
    # Check if we have any content at all
    has_content = any([
        data.get("name"),
        data.get("contact", {}).get("phone"),
        data.get("contact", {}).get("email"),
        data.get("contact", {}).get("location"),
        contact_links,
        data.get("summary"),
        skills_content,
        experience_content,
        education_content,
        awards_content,
        certifications_content,
        publications_content
    ])
    
    # If no content at all, provide a minimal template
    if not has_content:
        template = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{ragged2e}

% Setup hyperref for colored links
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=blue,
}

% Page styling
\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Fix footskip warning
\setlength{\footskip}{5pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

%-------------------------
% Custom commands
\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-4pt}}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

% Name at the top
\begin{flushleft}{\LARGE \textbf{Resume}}
\end{flushleft}
\vspace{-10pt}
\noindent{\rule{\linewidth}{0.4pt}}

\vspace{3pt}


\end{document}"""
    
    # Replace the placeholders in the template
    filled_template = template
    filled_template = filled_template.replace("NAME", escape_latex(data.get("name", "Resume")))
    
    # Handle contact information conditionally
    phone = data.get("contact", {}).get("phone", "")
    email = data.get("contact", {}).get("email", "")
    location = data.get("contact", {}).get("location", "")
    
    # Only include contact section if at least one field has content
    has_contact_info = any([phone, email, location, contact_links])
    
    if has_contact_info:
        # Build contact information dynamically based on available fields
        contact_parts = []
        
        # Build left side of the table
        left_parts = []
        if phone:
            left_parts.append(f"Phone: {escape_latex(phone)}")
        if email:
            left_parts.append(f"Email: {escape_latex(email)}")
        
        # Build right side of the table
        right_parts = []
        if contact_links:
            right_parts.append(contact_links)
        if location:
            right_parts.append(f"Location: {escape_latex(location)}")
        
        # Create the contact table
        if left_parts and right_parts:
            # Both sides have content
            contact_table = "\\begin{tabular*}{\\textwidth}{l@{\\extracolsep{\\fill}}r}\n  " + " & ".join(left_parts) + " \\\\\n  " + " & ".join(right_parts) + "\n\\end{tabular*}"
        elif left_parts:
            # Only left side has content
            contact_table = "\\begin{tabular*}{\\textwidth}{l}\n  " + " \\\\\n  ".join(left_parts) + "\n\\end{tabular*}"
        elif right_parts:
            # Only right side has content
            contact_table = "\\begin{tabular*}{\\textwidth}{r}\n  " + " \\\\\n  ".join(right_parts) + "\n\\end{tabular*}"
        else:
            # This shouldn't happen since we checked has_contact_info
            contact_table = ""
        
        # Replace the contact section with our dynamic table
        # Use string replacement instead of regex to avoid escape issues
        old_contact_section = """% Contact information with links on the same line
\\begin{tabular*}{\\textwidth}{l@{\\extracolsep{\\fill}}r}
  Phone: PHONE & Email: EMAIL \\\\
  LINKS & Location: LOCATION
\\end{tabular*}"""
        new_contact_section = f"""% Contact information with links on the same line
{contact_table}"""
        filled_template = filled_template.replace(old_contact_section, new_contact_section)
    else:
        # Remove the entire contact information section
        filled_template = re.sub(r'% Contact information with links on the same line\s*\\begin\{tabular\*\}\{\\textwidth\}\{l@\{\\extracolsep\{\\fill\}\}r\}\s*Phone: PHONE & Email: EMAIL \\\\\s*LINKS & Location: LOCATION\s*\\end\{tabular\*\}', '', filled_template)
    
    # Handle summary conditionally
    summary = data.get("summary", "")
    if summary:
        filled_template = filled_template.replace("SUMMARY", escape_latex(summary))
    else:
        # Remove the entire summary section
        filled_template = re.sub(r'% Professional Summary\s*\\section\{Professional Summary\}\s*\\justifying\s*SUMMARY', '', filled_template)
    
    # Only include sections that have content
    if skills_content:
        filled_template = filled_template.replace("SKILLS", skills_content)
    else:
        # Remove the skills section entirely
        filled_template = re.sub(r'% Technical Skills\s*\\section\{Technical Skills\}\s*\\resumeSubHeadingListStart\s*SKILLS\s*\\resumeSubHeadingListEnd', '', filled_template)
    
    if experience_content:
        filled_template = filled_template.replace("EXPERIENCE", experience_content)
    else:
        # Remove the experience section entirely
        filled_template = re.sub(r'% Experience\s*\\section\{Professional Experience\}\s*\\resumeSubHeadingListStart\s*EXPERIENCE\s*\\resumeSubHeadingListEnd', '', filled_template)
    
    if education_content:
        filled_template = filled_template.replace("EDUCATION", education_content)
    else:
        # Remove the education section entirely
        filled_template = re.sub(r'% Education\s*\\section\{Education\}\s*\\resumeSubHeadingListStart\s*EDUCATION\s*\\resumeSubHeadingListEnd', '', filled_template)
    
    if awards_content:
        filled_template = filled_template.replace("AWARDS", awards_content)
    else:
        # Remove the awards section entirely
        filled_template = re.sub(r'% Awards\s*\\section\{Awards and Honors\}\s*\\resumeSubHeadingListStart\s*AWARDS\s*\\resumeSubHeadingListEnd', '', filled_template)
    
    if certifications_content:
        filled_template = filled_template.replace("CERTIFICATIONS", certifications_content)
    else:
        # Remove the certifications section entirely
        filled_template = re.sub(r'% Certifications\s*\\section\{Certifications\}\s*\\resumeSubHeadingListStart\s*CERTIFICATIONS\s*\\resumeSubHeadingListEnd', '', filled_template)
    
    if publications_content:
        filled_template = filled_template.replace("PUBLICATIONS", publications_content)
    else:
        # Remove the publications section entirely
        filled_template = re.sub(r'% Publications\s*\\section\{Selected Publications\}\s*\\begin\{enumerate\}\[noitemsep, leftmargin=\*,label=\{\[\\arabic\*\]\}\]\s*PUBLICATIONS\s*\\end\{enumerate\}', '', filled_template)
    
    # Write the filled template to the output file
    with open(output_path, 'w') as file:
        file.write(filled_template)
    
    return output_path

def compile_latex(latex_file, output_format="pdf", data=None):
    """Compile the LaTeX file to PDF"""
    try:
        # Always use 'resume' as the output name
        output_name = "resume"
        
        # Set paths
        output_dir = OUTPUT_DIR
        output_pdf = os.path.join(output_dir, f"{output_name}.pdf")
        
        # Make sure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run pdflatex command directly in the output directory
        latex_file_abs = os.path.abspath(latex_file)
        current_dir = os.getcwd()
        
        try:
            os.chdir(output_dir)
            
            # Run pdflatex
            cmd = ["pdflatex", "-interaction=nonstopmode", f"-jobname={output_name}", latex_file_abs]
            print(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Check if compilation was successful
            if result.returncode != 0:
                error_msg = f"LaTeX compilation failed with return code {result.returncode}. Error output: {result.stderr}"
                print(f"Error compiling LaTeX: {result.stderr}")
                return None, error_msg
            
            # Check if the PDF was created
            if not os.path.exists(f"{output_name}.pdf"):
                error_msg = f"PDF file not generated. Current directory: {os.getcwd()}, Files: {os.listdir('.')}"
                print(f"Error: PDF file not generated")
                print(f"Current directory: {os.getcwd()}")
                print(f"Files in directory: {os.listdir('.')}")
                return None, error_msg
            
            # Copy the PDF to the output directory if we're not already there
            pdf_path = os.path.join(output_dir, f"{output_name}.pdf")
            
            return pdf_path, None
            
        finally:
            # Return to the original directory
            os.chdir(current_dir)
            
            # Clean up auxiliary files
            aux_files = [
                os.path.join(output_dir, f"{output_name}.aux"),
                os.path.join(output_dir, f"{output_name}.log"),
                os.path.join(output_dir, f"{output_name}.out"),
                os.path.join(output_dir, f"{output_name}.fdb_latexmk"),
                os.path.join(output_dir, f"{output_name}.fls"),
                os.path.join(output_dir, f"{output_name}.synctex.gz"),
                os.path.join(output_dir, f"{output_name}.toc"),
                os.path.join(output_dir, f"{output_name}.nav"),
                os.path.join(output_dir, f"{output_name}.snm"),
                os.path.join(output_dir, f"{output_name}.vrb")
            ]
            
            for file in aux_files:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        print(f"Cleaned up: {os.path.basename(file)}")
                    except Exception as e:
                        print(f"Warning: Could not remove {file}: {e}")
    
    except Exception as e:
        error_msg = f"Exception during LaTeX compilation: {str(e)}"
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, error_msg

def cleanup_auxiliary_files(output_dir=None, current_dir=True):
    """
    Clean up LaTeX auxiliary files from specified directories
    
    Args:
        output_dir: Directory to clean up (defaults to OUTPUT_DIR)
        current_dir: Whether to also clean up current directory
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    aux_extensions = [
        '.aux', '.log', '.out', '.fdb_latexmk', '.fls', '.synctex.gz',
        '.toc', '.nav', '.snm', '.vrb'
    ]
    
    files_cleaned = 0
    
    # Clean up files in output directory
    for ext in aux_extensions:
        # Clean up resume.* files
        resume_aux_file = os.path.join(output_dir, f"resume{ext}")
        if os.path.exists(resume_aux_file):
            try:
                os.remove(resume_aux_file)
                print(f"Cleaned up: {os.path.basename(resume_aux_file)}")
                files_cleaned += 1
            except Exception as e:
                print(f"Warning: Could not remove {resume_aux_file}: {e}")
        
        # Clean up template.* files
        template_aux_file = os.path.join(output_dir, f"template{ext}")
        if os.path.exists(template_aux_file):
            try:
                os.remove(template_aux_file)
                print(f"Cleaned up: {os.path.basename(template_aux_file)}")
                files_cleaned += 1
            except Exception as e:
                print(f"Warning: Could not remove {template_aux_file}: {e}")
    
    # Also clean up current directory if requested
    if current_dir:
        for ext in aux_extensions:
            # Clean up resume.* files in current directory
            resume_aux_file = f"resume{ext}"
            if os.path.exists(resume_aux_file):
                try:
                    os.remove(resume_aux_file)
                    print(f"Cleaned up from current directory: {resume_aux_file}")
                    files_cleaned += 1
                except Exception as e:
                    print(f"Warning: Could not remove {resume_aux_file}: {e}")
            
            # Clean up template.* files in current directory
            template_aux_file = f"template{ext}"
            if os.path.exists(template_aux_file):
                try:
                    os.remove(template_aux_file)
                    print(f"Cleaned up from current directory: {template_aux_file}")
                    files_cleaned += 1
                except Exception as e:
                    print(f"Warning: Could not remove {template_aux_file}: {e}")
    
    return files_cleaned

def main():
    """Main function to generate resume"""
    try:
        # Check if a JSON file was specified as a command line argument
        json_file = 'resume.json'
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            json_file = sys.argv[1]
            print(f"Using JSON file: {json_file}")
        
        # Load data from JSON file
        data = load_resume_data(json_file)
        
        # Generate LaTeX file from template and data (with firstname_lastname)
        latex_file = generate_latex_resume(data)
        print(f"Generated LaTeX file: {latex_file}")
        
        # Compile LaTeX to PDF
        pdf_file, error_msg = compile_latex(latex_file, data=data)
        if pdf_file:
            print(f"Generated PDF file: {pdf_file}")
            
            # Clean up auxiliary files using the new function
            files_cleaned = cleanup_auxiliary_files()
            print(f"Cleaned up {files_cleaned} auxiliary files")
                        
            print(f"\nSuccess! Your resume has been generated at: {pdf_file}")
        else:
            print(f"Failed to generate PDF. Please check LaTeX errors: {error_msg}")
    
    except Exception as e:
        print(f"Error generating resume: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 