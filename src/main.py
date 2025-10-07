from celery.result import AsyncResult
from tasks import calculate_pi_with_things, app as celery_app
from flask import Flask, request, jsonify
from flasgger import Swagger
app = Flask(__name__)
swagger = Swagger(app)

@app.route('/calculate_pi')
def calculate_pi():
    """
    Calculate Pi to a specified number of digits.
    ---
    parameters:
      - name: n
        in: query
        type: integer
        required: true
        description: The number of digits of Pi to calculate.
    responses:
      200:
        description: The task ID for the Pi calculation.
        schema:
          id: task_id
          properties:
            id:
              type: string
              description: The ID of the task.
      400:
        description: Invalid input. 'n' is required.
    """
    n = request.args.get('n', type=int)
    if n is None:
        return jsonify({"error": "Please provide n as integer"}), 400
    task = calculate_pi_with_things.delay(n)
    return {"id": str(task.id)}


@app.route("/check_progress/<task_id>")
def check_progress(task_id):
    """
    Check the progress of a Pi calculation task.
    ---
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
        description: The ID of the task to check.
    responses:
      200:
        description: The progress of the task.
        schema:
          id: task_progress
          properties:
            comment:
              type: string
              description: A comment about the task progress (may be not defined)
            state:
              type: string
              description: The state of the task.
              enum: ["PROGRESS", "FINISHED", "UNKNOWN"]
            progress:
              type: number
              description: The progress of the task from 0 to 1.
            result:
              type: string
              description: The result of the task (the calculated value of Pi) or an error message/object.
    """
    result = AsyncResult(task_id, app=celery_app)
    if result.state == 'PENDING':
        # job did not start yet
        response = {
            'state': "PROGRESS",
            'progress': 0,
            'result': None
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': "FINISHED",
            'progress': 1,
            'result': (result.result["result"])
        }
    elif result.state != 'FAILURE':
        response = result.info
        response["state"] = "PROGRESS"
        if 'result' not in response:
            response['result'] = None
    else:
        # something went wrong in the background job
        response = {
            'state': "UNKNOWN",
            'progress': result.info.get('progress', 0),
            'result': (result.info),
        }
    return response

app.run(host='0.0.0.0', port=5000, debug=True)
