from typing import List

import boto3
from fastapi import FastAPI, Query
from handler.agents_for_bedrock import AgentsForBedrock
from mangum import Mangum
from pydantic import BaseModel, Field

app = FastAPI()

ec2_client= boto3.client("ec2", region_name="us-east-1")


class list_response(BaseModel):
    InstanceIds: List[str] = Field(description="List of instances.")

class describe_request(BaseModel):
    InstanceId: str = Field(description="The instance ID.")

class describe_response(BaseModel):
    InstanceName: str = Field(description="The name of the instance.")
    StateName: str = Field(description="The state of the instance ( pending | running | shutting-down | terminated | stopping | stopped).")


@app.get("/list", description="""
Returns instance ID for all instances.
If you need information such as the name or status of an instance, use the /describe API to obtain it.
""")
def list_instances() -> list_response:

    response = ec2_client.describe_instances(
        MaxResults=10
    )

    InstanceIds = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            InstanceIds.append(instance["InstanceId"])

    return {"InstanceIds": InstanceIds}


@app.post("/describe", description="""
Describe instance. Returns the name and status of the instance.
""")
def describe_instance(request: describe_request) -> describe_response:

    print(request)

    response = ec2_client.describe_instances(
        InstanceIds=[request.InstanceId],
    )

    print(request)

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:

            tags = instance.get("Tags", [{}])
            instance_name = list(filter(lambda x: x["Key"] == "Name", tags))
            instance_name = instance_name[0]["Value"] if len(instance_name) > 0 else request.InstanceId

            response = describe_response(
                InstanceName=instance_name,
                StateName=instance["State"]["Name"]
            )

            return response

    raise Exception()


lambda_handler = Mangum(app,
                 custom_handlers=[AgentsForBedrock], 
                 lifespan="off")
