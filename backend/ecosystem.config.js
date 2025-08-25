module.exports = {
    apps: [
      {
        name: "ai_email_dossier_stag",   // process name
        script: "app.py",                // your Python entry file
        cwd: "/home/azureuser/ai_email_dossier/stag/ai_email_dossier_agentic_ai/backend", // working dir
        interpreter: "./venv/bin/python3", // run with venv python
        instances: 1,                    // change to "max" for cluster mode
        autorestart: true,
        watch: false,
        max_memory_restart: "500M",
        env: {
          ENV: "staging",
          PORT: 5000
        }
      }
    ]
  };