import { GoogleGenerativeAI } from "@google/generative-ai";
import fs from 'fs';
import path from 'path';

// Manual env reading to avoid dependency issues
const envPath = path.resolve(process.cwd(), '.env');
const envContent = fs.readFileSync(envPath, 'utf8');
const match = envContent.match(/VITE_GEMINI_API_KEY=(.*)/);
const API_KEY = match ? match[1].trim() : null;

if (!API_KEY) {
  console.error("VITE_GEMINI_API_KEY is not set in .env file");
  process.exit(1);
}

async function listModels() {
  try {
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${API_KEY}`);
    const data = await response.json();
    
    if (data.error) {
      console.error("API Error:", data.error.message);
      return;
    }

    console.log("\nAvailable Gemini Models:");
    data.models.forEach(model => {
      console.log(`- ${model.name.replace('models/', '')}: ${model.displayName}`);
    });
    console.log("\n");
  } catch (error) {
    console.error("Error listing models:", error);
  }
}

listModels();
