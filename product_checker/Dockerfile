FROM public.ecr.aws/lambda/python:3.14

# For real-time logging
ENV PYTHONUNBUFFERED=1

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY tracked_product_checker.py lambda_handler.py ./

CMD ["lambda_handler.lambda_handler"]
