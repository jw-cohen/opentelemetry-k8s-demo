#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import grpc

import demo_pb2
import demo_pb2_grpc

from logger import getJSONLogger
logger = getJSONLogger('emailservice-client')

from opencensus.trace.tracer import Tracer
from opencensus.trace.exporters import stackdriver_exporter
from opencensus.trace.ext.grpc import client_interceptor

from opentelemetry import trace
from opentelemetry.exporter import jaeger
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

# try:
#     exporter = stackdriver_exporter.StackdriverExporter()
#     tracer = Tracer(exporter=exporter)
#     tracer_interceptor = client_interceptor.OpenCensusClientInterceptor(tracer, host_port='0.0.0.0:8080')
# except:
#     tracer_interceptor = client_interceptor.OpenCensusClientInterceptor()

def send_confirmation_email(email, order):

  trace.set_tracer_provider(TracerProvider())
  tracer = trace.get_tracer(__name__)
  jaeger_exporter = jaeger.JaegerSpanExporter(
      service_name="emailservice",
      collector_endpoint="http://otel-agent:14268/api/traces",
  )

  span_processor = BatchExportSpanProcessor(jaeger_exporter)

  # add to the tracer factory
  trace.get_tracer_provider().add_span_processor(span_processor)
  trace.get_tracer_provider().add_span_processor(
      SimpleExportSpanProcessor(ConsoleSpanExporter())
  )

  grpc_client_instrumentor = GrpcInstrumentorClient()
  grpc.client_instrumentor.instrument()

  channel = grpc.insecure_channel('0.0.0.0:8080')
  # channel = grpc.intercept_channel(channel, tracer_interceptor)
  stub = demo_pb2_grpc.EmailServiceStub(channel)
  try:
    response = stub.SendOrderConfirmation(demo_pb2.SendOrderConfirmationRequest(
      email = email,
      order = order
    ))
    logger.info('Request sent.')
  except grpc.RpcError as err:
    logger.error(err.details())
    logger.error('{}, {}'.format(err.code().name, err.code().value))

if __name__ == '__main__':
  logger.info('Client for email service.')