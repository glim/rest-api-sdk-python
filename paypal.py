import httplib2, base64, json, re

class Api:

  # Create API object
  # == Example
  #   import paypal
  #   api = paypal.Api( client_id='CLIENT_ID', client_secret='CLIENT_SECRET', ssl_options={} )
  def __init__(self, **args):
    self.endpoint       = args.get("endpoint", "https://api.sandbox.paypal.com")
    self.token_endpoint = args.get("token_endpoint", self.endpoint)
    self.client_id      = args.get("client_id")
    self.client_secret  = args.get("client_secret")
    self.token          = args.get("token")
    self.ssl_options    = args.get("ssl_options", {})

  # Find basic auth
  def basic_auth(self):
    return base64.encodestring('%s:%s' % (self.client_id, self.client_secret)).replace('\n', '')

  # Generate token
  def get_token(self):
    if self.token == None :
      token_hash = self.request(self.join_url(self.token_endpoint, "/v1/oauth2/token"), "POST",
          body = "response_type=token&grant_type=client_credentials",
          headers = { "Authorization": ("Basic %s" % self.basic_auth()), "Accept": "application/json" } )
      self.token = token_hash['access_token']
    return self.token

  # Join given url
  # == Example
  #   api.join_url("example.com", "index.html") # Return "example.com/index.html"
  def join_url(self, url, path):
    return re.sub(r'/?$', re.sub(r'^/?', '/', path), url)

  # Make HTTP call and Format Response
  # == Example
  #   api.request("https://api.sandbox.paypal.com/v1/payments/payment?count=10", "GET")
  #   api.request("https://api.sandbox.paypal.com/v1/payments/payment", "POST", "{}" )
  def request(self, url, method, body = None, headers = None):
    http = httplib2.Http(**self.ssl_options)
    headers = headers or self.headers()
    response, data = http.request(url, method, body= body, headers= headers)

    if(response.status >= 200 and response.status <= 299):
      return json.loads(data)

    elif(response.status == 400 and response['content-type'] == "application/json"): # Format Response error message
      return { "error": json.loads(data) }

    elif(response.status == 401 and self.token and self.client_id): # Handle Expire token
      self.token = None
      return self.request(url, method, body)

    else: # Raise Exception
      raise Exception(response.reason)

  # Default HTTP headers
  def headers(self):
    return { "Authorization": ("Bearer %s" % self.get_token()), "Content-Type": "application/json", "Accept": "application/json" }

  # Make GET request
  # == Example
  #   api.get("v1/payments/payment?count=1")
  #   api.get("v1/payments/payment/PAY-1234")
  def get(self, action):
    return self.request(self.join_url(self.endpoint, action), 'GET' )

  # Make POST request
  # == Example
  #   api.post("v1/payments/payment", { 'indent': 'sale' })
  #   api.post("v1/payments/payment/PAY-1234/execute", { 'payer_id': '1234' })
  def post(self, action, params = {}):
    return self.request(self.join_url(self.endpoint, action), 'POST', body= json.dumps(params) )


