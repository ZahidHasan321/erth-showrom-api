# Use the AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.13

# Set the working directory
WORKDIR /var/task

# Copy only the requirements file first to take advantage of Docker caching
COPY requirements.txt .

# Install Python dependencies. This uses pip from the base image.
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m compileall -O /var/task

RUN rm -rf /var/cache/pip /root/.cache
# Copy the rest of your application code
COPY . .

# Set the command to run your Mangum handler.
# Format: [filename without .py].[Mangum handler object name]
# Since your handler is named 'handler' in 'main.py':
CMD ["main.handler"]