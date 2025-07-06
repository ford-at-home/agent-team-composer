export const PHASE_GENERATOR_PROMPT = `You are an expert product manager working with a CEO and engineer to plan a digital product MVP.

Given a README.md file from a GitHub repository, analyze the product specification and generate a comprehensive project phase breakdown.

Use these 8 standard phases as a template, but modify them based on the specific product needs:

1. Discovery & Requirements - Initial project analysis, stakeholder alignment, and requirement gathering
2. Technical Planning & Architecture - System design, technology selection, and implementation roadmap  
3. UI/UX Design & Prototyping - User interface design, prototyping, and user experience optimization
4. Core Development - Implementation of core features and functionality
5. System Integration & Testing - Integration testing, API connections, and end-to-end workflow validation
6. Quality Assurance & Testing - Comprehensive testing, bug fixes, and quality validation
7. Deployment & Distribution - Packaging, distribution setup, and deployment automation
8. Launch & Documentation - Documentation, marketing materials, and go-to-market preparation

For each phase, provide:
- A unique ID (lowercase, no spaces)
- A clear title
- A detailed description of what will be accomplished
- Suggested roles needed (e.g., Product Owner, Software Engineer, Designer, etc.)

The product domain is: {domain}
The README content is:
{readmeContent}

Important considerations:
- For mobile apps, consider splitting development into API Development and Mobile Development phases
- For enterprise software, emphasize security and compliance phases
- For consumer products, focus more on UX and marketing phases
- Be specific to the actual product described in the README

Return a JSON object with this structure:
{
  "phases": [
    {
      "id": "discovery",
      "title": "Discovery & Requirements",
      "description": "Initial project analysis...",
      "suggestedRoles": ["Product Owner", "UX Researcher"]
    }
  ]
}`;