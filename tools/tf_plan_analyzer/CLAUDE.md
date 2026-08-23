# Terraform Plan Analyzer

## Overview

Terraform Plan Analyzer is a deterministic Python application that converts Terraform plan JSON output into a human-readable report.

The application DOES NOT execute Terraform commands and MUST NOT interact with Terraform state files directly.

Its only responsibility is to analyze an existing `tfplan.json` file and generate human-readable outputs.

The project MUST NOT use any AI services.

All outputs MUST be generated using Python only.

### Goals

- Generate human-readable Terraform plan summaries.
- Identify resource changes.
- Provide risk analysis based on Terraform changes.
- Produce pipeline-friendly outputs.
- Generate Markdown and HTML reports.
- Remain deterministic and predictable.

---

## Project Scope

### Supported Input

The Terraform Plan Analyzer ONLY accepts the following input:

```
tfplan.json
```

The JSON file MUST already exist before the application is executed.

This project MUST NOT:

- Execute `terraform plan`
- Execute `terraform apply`
- Execute `terraform destroy`
- Execute `terraform show`
- Read Terraform state files directly
- Perform any infrastructure changes

Generating the Terraform plan is outside the scope of this project.

### Example Workflow

```
Terraform Pipeline
       |
terraform plan -out=tfplan
       |
terraform show -json tfplan
       |
     tfplan.json
       |
-----------------------------
| Terraform Plan Analyzer   |
-----------------------------
       |
     Parser
       |
   Resource Analyzer
       |
    Risk Analysis
       |
      Reporters
       |
-----------------------------
| Markdown Report           |
| HTML Report               |
| Pipeline Summary          |
-----------------------------
```

The Terraform Plan Analyzer ONLY consumes:

```
tfplan.json
```

---

## Rules

### Claude MUST NOT

- Add AI integrations.
- Add LLM APIs.
- Add OpenAI APIs.
- Add Anthropic APIs.
- Use machine learning libraries.
- Use cloud services for analysis.
- Execute Terraform commands.
- Modify Terraform files.
- Read or modify Terraform state files.
- Mix parsing, analysis, and reporting logic.

### Claude MUST

- Use deterministic Python implementations.
- Follow SOLID principles.
- Write unit tests.
- Keep modules reusable.
- Follow clean architecture.
- Keep analyzers service specific.
- Maintain separation of concerns.
- Support future service analyzers without changing the parser implementation.

---

## Project Structure

```
terraform-plan-analyzer/

    parser/
        tfplan_parser.py

    analyzers/
        lambda.py
        sqs.py
        eventbridge.py
        iam.py
        security_group.py
        s3.py
        vpc.py
        subnet.py
        dynamodb.py
        generic.py

    reporters/
        markdown.py
        html.py
        pipeline.py

    risks/
        risk_analyzer.py

    models/
        resource.py
        change.py

    utils/
        helpers.py

    tests/

    main.py
```

---

## Resource Analysis

Every resource analyzer MUST identify:

- Creates
- Updates
- Replacements
- Deletes

Every analyzer MUST provide:

- Resource name
- Resource type
- Action performed
- Important attribute changes
- Possible impacts
- Resource dependencies
- Risk level

### Supported Actions

Examples:

```
Create
-------

aws_lambda_function

Update
-------

aws_security_group

Replace
--------

aws_vpc

Delete
------

aws_iam_role
```

---

## Service Analyzers

Every Terraform resource SHOULD have its own analyzer implementation.

Examples:

```
analyzers/

    lambda.py
    sqs.py
    eventbridge.py
    security_group.py
    iam.py
    s3.py
    vpc.py
    subnet.py
    dynamodb.py
    generic.py
```

If an analyzer does not exist, the resource MUST automatically fall back to:

```
generic.py
```

The generic analyzer MUST provide:

- Resource name
- Resource type
- Action performed
- Before values
- After values
- Risk level if applicable

Unsupported resources MUST NOT fail the application.

---

## Risk Analysis

### HIGH

Examples:

- Deleting RDS resources
- Replacing VPC resources
- Replacing Security Groups
- Deleting IAM roles
- Deleting KMS keys
- Replacing Route Tables

### MEDIUM

Examples:

- Replacing Lambda functions
- Replacing EventBridge rules
- Updating Security Group rules
- Replacing API Gateway resources

### LOW

Examples:

- Updating tags
- Updating descriptions
- Adding outputs
- Minor configuration changes

Risk analysis MUST remain deterministic.

Risk levels MUST be determined only from Terraform resource changes.

No AI-generated risk assessments are allowed.

---

## Report Requirements

Reports MUST be human-readable.

Example:

```
Terraform Plan Summary

----------------------------------

Resources to Create : 3
Resources to Update : 2
Resources to Delete : 1
Resources to Replace : 1

----------------------------------

Lambda

Create:

- email-ingestion-lambda

Changes:

- runtime = python3.13
- memory = 256 MB

Impact:

- A new Lambda function will be created.

Risk:

- LOW


----------------------------------

Security Group

Update:

Changes:

Before:

- Port 80
- Port 443

After:

- Port 443
- Port 8080

Impact:

- Application traffic rules will change.

Risk:

- MEDIUM


----------------------------------

HIGH RISK

- The VPC resource will be replaced.
- Existing network resources may experience downtime.

----------------------------------
```

Reports SHOULD include:

- Resource summaries
- Risk summaries
- Important configuration changes
- Impact summaries
- Pipeline-friendly output

---

## Coding Standards

Claude MUST:

- Use Python type hints.
- Use dataclasses where appropriate.
- Keep functions small and reusable.
- Create unit tests.
- Follow SOLID principles.
- Separate parsing from analysis.
- Separate analysis from reporting.
- Keep resource analyzers independent.

Claude MUST NOT:

- Create monolithic files.
- Hardcode Terraform resources.
- Duplicate logic across analyzers.
- Mix business logic with report generation.
- Introduce AI dependencies.

---

## Future Support

### Additional Service Analyzers

Examples:

- ECS
- EKS
- RDS
- ACM
- CloudFront
- SNS
- API Gateway
- Route53
- CloudWatch
- Secrets Manager
- Step Functions
- Bedrock
- OpenSearch
- WAF
- ALB
- NLB

### Future Outputs

- Markdown reports
- HTML reports
- Azure DevOps pipeline summaries
- Pull Request comments
- Slack notifications

The implementation MUST remain deterministic and MUST NOT require any AI services.

The ONLY expected input for this project is:

```
tfplan.json
```

All analysis MUST be performed exclusively from the contents of the Terraform plan JSON file.