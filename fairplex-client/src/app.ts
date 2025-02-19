import express from 'express';
import session from 'express-session';
import * as client from 'openid-client'
import { jwtDecode, JwtPayload } from "jwt-decode";
import cookieParser from 'cookie-parser';
import jwt, { JsonWebTokenError } from 'jsonwebtoken';
import jwkToPem from 'jwk-to-pem';
import bodyParser from 'body-parser';

// Extend express-session declarations
declare module 'express-session' {
  interface SessionData {
    code_verifier?: string;
    // id_token?: string;
    // access_token?: string;
    state?: string;
    // payload?: any;
    accessTokenDecoded?: JwtPayload;
    idTokenDecoded?: JwtPayload;
    passportToken? : string;
    passportTokenDecoded?: JwtPayload;
    // pemId?: string;
    // pemAccess?: string;
    idTokenVerified? : boolean;
    accessTokenVerified? : boolean;
    passportTokenVerified? : boolean;
    destinationAmpPdGCSUrl? : string;
    sourceAmpPdDRSUrl? : string;
    ampPdDataTransferredTo? : string;
    ampPdDataTransferredMessage? : string;
  }
}

const app = express();
const port = 5554;

// Configure session middleware
app.use(
  session({
    secret: 'your-secret-key',
    resave: false,
    saveUninitialized: true,
  })
);
app.use(cookieParser());
app.use(bodyParser.urlencoded({extended:false}))

// let server: URL = new URL('http://hydra:4444/.well-known/openid-configuration') // Authorization Server's Issuer Identifier
let server: URL = new URL(`${process.env.HYDRA_URL}/.well-known/openid-configuration`) // Authorization Server's Issuer Identifier
let clientId: string = process.env.HYDRA_CLIENT_ID! // Client identifier at the Authorization Server
let clientSecret: string = process.env.HYDRA_CLIENT_SECRET! // Client Secret

let config: client.Configuration = await client.discovery(
  server,
  clientId,
  clientSecret,
  undefined,
  {
    execute: [client.allowInsecureRequests],
  },
)

// Serve the login page
app.get('/', (req: express.Request, res: express.Response) => {
  const idToken = req.cookies.idToken || 'Not authenticated';
  const decodedIdToken = req.session.idTokenDecoded || 'Not authenticated';
  const accessToken = req.cookies.accessToken || 'Not authenticated';
  const decodedAccessToken = req.session.accessTokenDecoded || 'Not authenticated';
  const passportToken = req.session.passportToken || 'Not authenticated';
  const decodedPassportToken = req.session.passportTokenDecoded || 'Not authenticated';
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>FAIRplex GA4GH Federated Authentication Pilot</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .token-display { 
            word-break: break-all; 
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
          }
          .label1 {
            display: block;
            width: 30ch;
            background-color: light-gray;
          }
        </style>
      </head>
      <body>
        <h1>FAIRplex GA4GH Federated Authentication Pilot</h1>
        <button onclick="window.location.href='/login'">Login</button>
        ${req.session.idTokenDecoded
        ? `<div class="token-display">
                <h3>OpenID Token:</h3>
                <p>${idToken}</p>
               </div>
               <div class="token-display">
                <h3>OpenID Token Payload:</h3>
                <pre>${JSON.stringify(decodedIdToken, null, 2)}</pre>
                <bold>Signature verified: ${req.session.idTokenVerified}</bold>
              </div>
          <div class="token-display">
                <h3>OAuth2 Access Token:</h3>
                <p>${accessToken}</p>
               </div>
               <div class="token-display">
                <h3>OAuth2 Access Token Payload:</h3>
                <pre>${JSON.stringify(decodedAccessToken, null, 2)}</pre>
                <bold>Signature verified: ${req.session.accessTokenVerified}</bold>
              </div>
          <div class="token-display">
                <h3>GA4GH Passport Token:</h3>
                <p>${passportToken}</p>
               </div>
               <div class="token-display">
                <h3>GA4GH Passport Payload:</h3>
                <pre>${JSON.stringify(decodedPassportToken, null, 2)}</pre>
                <bold>Signature verified: ${req.session.accessTokenVerified}</bold>
              </div>
          <br>
          <hr>
          <h3>AMP PD Data Transfer</h3>
          <form action="/transfer-amp-pd-data" method="POST">
          <label for="amp-pd-data-source" class="label1">Source DRS URI</label>
            <input type="text" id="amp-pd-data-source" name="amp-pd-data-source" size="100" 
              value=${req.session.sourceAmpPdDRSUrl}><br><br>
          <label for="amp-pd-data-destination" class="label1">Destination Bucket</label>
            <input type="text" id="amp-pd-data-destination" name="amp-pd-data-destination" size="100" 
              value=${req.session.destinationAmpPdGCSUrl}><br><br>
            <input type="submit" value="Transfer AMP PD Data">
          </form>
              `
        : ''
        }
        ${req.session.ampPdDataTransferredMessage
        ? `<div class="token-display">
                <h4>AMP PD Data Transferred To:</h4>
                <p>${req.session.ampPdDataTransferredTo}</p>
                <h4>Message:</h4>
                <p>${req.session.ampPdDataTransferredMessage}</p>
            </div>`
        : ''
        }

      </body>
    </html>
  `;
  res.send(html);
});

function parseGCSUri(uri: string) {
  if (!uri.startsWith('gs://')) {
    throw new Error('Invalid GCS URI: Must start with "gs://"');
  }

  const parts = uri.substring(5).split('/');
  const bucket = parts[0];
  const path = parts.slice(1).join('/');

  return { bucket, path };
}

// A separate search/discovery mechanism will provide the actual DRS URI for the requested data object
const AMP_PD_DRS_URI:string = process.env.AMP_PD_DRS_URI!
const AMP_PD_DESTINATION_URI:string = process.env.AMP_PD_DESTINATION_URI!

app.post('/transfer-amp-pd-data', async (req: express.Request, res: express.Response) => {
  console.log(`getting AMP PD data:${JSON.stringify(req.body)}`);
  req.session.sourceAmpPdDRSUrl = req.body['amp-pd-data-source']
  req.session.destinationAmpPdGCSUrl = req.body['amp-pd-data-destination']
  const {bucket:dest_bucket, path:dest_path} = parseGCSUri(req.session.destinationAmpPdGCSUrl!)
  const response = await fetch(req.session.sourceAmpPdDRSUrl!, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({'passports':[req.session.passportToken]}),
  
  });
  const data = await response.json()
  console.log(data)
  const AUTH_PILOT_DATA_TRANSFER_URL:string = process.env.AUTH_PILOT_DATA_TRANSFER_URL!
  const downloadresponse = await fetch(AUTH_PILOT_DATA_TRANSFER_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      'signed_url':data['signed_url'],
      'destination_bucket': dest_bucket,
      'destination_path': dest_path
    })  
  });

  const dataTransferResult = await downloadresponse.json()
  console.log(dataTransferResult)
  req.session.ampPdDataTransferredTo = dataTransferResult['gcs_url']
  req.session.ampPdDataTransferredMessage = dataTransferResult['message']

  res.redirect('/')
})

// Handle login initiation
app.get('/login', async (req: express.Request, res: express.Response) => {
  /**
 * Value used in the authorization request as the redirect_uri parameter, this
 * is typically pre-registered at the Authorization Server.
 */
  let redirect_uri: string = process.env.OAUTH_CALLBACK! // Redirect URI
  let scope: string = 'openid profile email ga4gh_passport_v1' // Scope of the access request
  /**
   * PKCE: The following MUST be generated for every redirect to the
   * authorization_endpoint. You must store the code_verifier and state in the
   * end-user session such that it can be recovered as the user gets redirected
   * from the authorization server back to your application.
   */
  let code_verifier: string = client.randomPKCECodeVerifier()
  let code_challenge: string = await client.calculatePKCECodeChallenge(code_verifier)
  let state: string = client.randomState()
  // Store the code_verifier in session for later use
  req.session.code_verifier = code_verifier;
  req.session.state = state

  let parameters: Record<string, string> = {
    redirect_uri,
    scope,
    code_challenge,
    code_challenge_method: 'S256',
    state,
  }

  // if (!config.serverMetadata().supportsPKCE()) {
  //   /**
  //    * We cannot be sure the server supports PKCE so we're going to use state too.
  //    * Use of PKCE is backwards compatible even if the AS doesn't support it which
  //    * is why we're using it regardless. Like PKCE, random state must be generated
  //    * for every redirect to the authorization_endpoint.
  //    */
  //   parameters.state = state
  // }

  let redirectTo: URL = client.buildAuthorizationUrl(config, parameters)

  // now redirect the user to redirectTo.href
  console.log('redirecting to', redirectTo.href)

  res.redirect(redirectTo.href);
});

// Handle the callback from the OIDC provider
app.get('/callback', async (req: express.Request, res: express.Response) => {
  try {
    // const params = client.callbackParams(req);

    if (!req.session.code_verifier) {
      throw new Error('Missing code_verifier in session');
    }
    const currentUrl = new URL(`${req.protocol}://${req.get('host')}${req.originalUrl}`);
    let tokens: client.TokenEndpointResponse = await client.authorizationCodeGrant(
      config,
      currentUrl,
      {
        pkceCodeVerifier: req.session.code_verifier,
        expectedState: req.session.state,
      },
      {
        tokenEndpointAuthMethod: 'client_secret_post',
      }
    )

    console.log('Token Endpoint Response', tokens)
    // Store the access token in session. NOT SECURE. DO NOT DO THIS.
    const decodedIdToken = jwtDecode(tokens.id_token!);
    req.session.idTokenDecoded = decodedIdToken;
    console.log('Decoded Id Token', decodedIdToken);
    const decodedAccessToken = jwtDecode(tokens.access_token);
    req.session.accessTokenDecoded = decodedAccessToken;
    console.log('Decoded Access Token', decodedAccessToken);

    // Get public key from JWKS endpoint
    const jwks_uri = config.serverMetadata().jwks_uri;
    console.log(jwks_uri);
    if (!jwks_uri) {
      throw new Error('Missing jwks_uri in server metadata');
    }
    let jwksResponse = await fetch(jwks_uri, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      }
    });
    const jwksData = await jwksResponse.json();
    console.log(JSON.stringify(jwksData['keys']))

    // Verify the id token using the public key
    for (const jwk of jwksData['keys']) {
      try {
        const pem_id = jwkToPem(jwk);
        // req.session.pemId = pem_id;
        const verifiedIdToken = jwt.verify(tokens.id_token!, pem_id, {algorithms: ['RS256']});
        req.session.idTokenVerified = verifiedIdToken !== undefined;
        console.log('Verified Id Token', verifiedIdToken);
      }
      catch(error) {
      }
    }

    // Verify the access token using the public key
    for (const jwk of jwksData['keys']) {
      try {
        const pemAccess = jwkToPem(jwk);
        // req.session.pemAccess = pemAccess;
        const verifiedAccessToken = jwt.verify(tokens.access_token, pemAccess, {algorithms: ['RS256']});
        req.session.accessTokenVerified = verifiedAccessToken !== undefined;
        console.log('Verified Access Token', verifiedAccessToken);
      }
      catch(error) {
      }
    }
    
    // Store the id token in a secure, HTTP-only cookie
    // Uh-oh, cookies are too big
    res.cookie('idToken', tokens.id_token, {
      httpOnly: true,
      secure: true, // Use in production
      sameSite: 'lax',
      maxAge: 3600000, // 1 hour in milliseconds
      path: '/'
    });
    // console.log('Decoded Id Token', decodedIdToken);
    // res.cookie('decodedIdToken', decodedIdToken, {
    //   httpOnly: true,
    //   secure: true, // Use in production
    //   sameSite: 'lax',
    //   maxAge: 3600000, // 1 hour in milliseconds
    //   path: '/'
    // });
    // // Store the access token in a secure, HTTP-only cookie
    res.cookie('accessToken', tokens.access_token, {
      httpOnly: true,
      secure: true, // Use in production
      sameSite: 'lax',
      maxAge: 3600000, // 1 hour in milliseconds
      path: '/'
    });
    // res.cookie('decodedAccessToken', decodedAccessToken, {
    //   httpOnly: true,
    //   secure: true, // Use in production
    //   sameSite: 'lax',
    //   maxAge: 3600000, // 1 hour in milliseconds
    //   path: '/'
    // });

    // Token exchange for passport
    const tokenExchangeUrl = process.env.AUTH_PILOT_TOKEN_EXCHANGE_URL!
    const response = await fetch(tokenExchangeUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: (new URLSearchParams({
        'grant_type' : 'urn:ietf:params:oauth:grant-type:token-exchange',
        'subject_token': tokens.access_token,
        'requested_token_type': 'urn:ga4gh:params:oauth:token-type:passport',
        'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token',
        'resource': AMP_PD_DRS_URI
      })).toString(),
    });

    const passportResult = await response.json();
    console.log('Passport Token exchange result', passportResult);
    // res.cookie('passportToken', passportResult.access_token, {
    //   httpOnly: true,
    //   secure: true, // Use in production
    //   sameSite: 'lax',
    //   maxAge: 3600000, // 1 hour in milliseconds
    //   path: '/'
    // });
    req.session.passportToken = passportResult.access_token;
    req.session.passportTokenDecoded = jwtDecode(passportResult.access_token);
    console.log('Decoded Passport Token', req.session.passportTokenDecoded);

    // Verify the passport token using the public key
    for (const jwk of jwksData['keys']) {
      try {
        const pemAccess = jwkToPem(jwk);
        const verifiedPassport = jwt.verify(passportResult.access_token, pemAccess, {algorithms: ['RS256']});
        req.session.passportTokenVerified = verifiedPassport !== undefined;
        console.log('Verified Passport Token', verifiedPassport);
      }
      catch(error) {
      }
    }

    req.session.sourceAmpPdDRSUrl = AMP_PD_DRS_URI
    req.session.destinationAmpPdGCSUrl = AMP_PD_DESTINATION_URI

    // Redirect back to the home page
    res.redirect('/');
  } catch (error) {
    console.error('Error during authentication:', error);
    res.status(500).send('Authentication failed');
  }
});

app.listen(port, () => {
  console.log(`App listening at http://127.0.0.1:${port}`);
});