# Faultline AWS Deployment

Faultline now has a deployable AWS MVP path.

This deploys:

- An encrypted, private S3 bucket for validation artifacts.
- A CloudWatch Logs group for AWS build output.
- An IAM role scoped to the artifact bucket and build logs.
- A CodeBuild project that checks out the GitHub repo, runs the Faultline offline validation suite on AWS, and writes proof artifacts to S3.

It does not yet run the full OpenTelemetry Demo in AWS. The CodeBuild project enables privileged Docker mode so the live demo path can be added later.

## Deploy

From the repo root:

```sh
aws cloudformation deploy \
  --stack-name faultline-mvp \
  --template-file infra/aws/cloudformation/faultline-mvp.json \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName=faultline \
    RepositoryUrl=https://github.com/sanjanasenthil/faultline.git \
    RepositoryBranch=main
```

Get the outputs:

```sh
aws cloudformation describe-stacks \
  --stack-name faultline-mvp \
  --query 'Stacks[0].Outputs'
```

Start the AWS validation run:

```sh
aws codebuild start-build --project-name faultline-validation
```

Watch logs:

```sh
aws logs tail /aws/codebuild/faultline-validation --follow
```

## What Counts As AWS Proof

For the project requirement, the minimum AWS proof is:

- The CloudFormation stack exists.
- The CodeBuild project runs on AWS.
- The build runs the Faultline test and compile checks.
- `results/aws-build/deployment-proof.md` appears in the artifact S3 bucket.
- CloudWatch Logs show the CodeBuild run.

## Local Validation

Before deploying, validate the template shape locally:

```sh
python3 scripts/validate_aws_template.py
```

This does not contact AWS. It only checks that the local template still includes S3, CloudWatch Logs, IAM, and CodeBuild.

## Costs And Cleanup

This stack can create AWS charges while resources exist. Clean it up after the demo:

```sh
aws cloudformation delete-stack --stack-name faultline-mvp
```

If the S3 bucket contains artifacts, empty it before deleting the stack.
