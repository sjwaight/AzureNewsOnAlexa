# Azure Functions - Alexa Skill backend built with Python

This repository contains a sample Azure Function that acts as the backend for an Alexa Skill.

In this sample Skill we are using the [Azure Updates site](https://azure.microsoft.com/updates/) as the data source, specifically using the RSS feed, to read Azure updates out to an Alexa user who invokes the "azure cloud news service".

If you want to run this sample and configure an Alexa Skill to use it you can follow this blog - (to be published).

You will need add two custom values to your `local.settings.json` file for the solution to run. A sample is shown below.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "UpdatesURL": "https://azure.microsoft.com/updates/feed/",
    "AlexaSkillID": "amzn1.ask.skill.YOUR_SKILL_ID_HERE"
  }
}
```