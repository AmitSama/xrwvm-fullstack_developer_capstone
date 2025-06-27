# Uncomment the required imports before adding the code
'''views for backend server for admin'''
import logging
import json
from django.contrib.auth.models import User
from django.contrib.auth import logout

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

@csrf_exempt
def login_user(request):
    '''Create a `login_request` view to handle sign in request'''
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

def logout_request(request):
    '''Create a `logout_request` view to handle sign out request'''
    logout(request) # Terminate user session CAlling Django build In Method
    data = {"userName":""} # Return empty username
    return JsonResponse(data)

@csrf_exempt
def register(request):
    '''Create a `registration` view to handle sign up request'''
    # Load JSON data from the request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    data = {"userName":username,"error":"Already Registered"}
    return JsonResponse(data)

def get_cars(request):
    '''helper to populate db'''
    count = CarMake.objects.filter().count()
    print(count)
    if count == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels":cars})

def get_dealerships(request, state="All"):
    '''Update the `get_dealerships`
    render list of dealerships all by default,
    particular state if state is passed'''
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})

def get_dealer_reviews(request, dealer_id):
    '''# Create a `get_dealer_reviews` view to render the reviews of a dealer'''
    # if dealer id has been provided
    if dealer_id is not None:
        endpoint = "/fetchReviews/dealer/"+str(dealer_id)
        reviews = get_request(endpoint)
        for review_detail in reviews:
            if review_detail['review'] is not None:
                response = analyze_review_sentiments(review_detail['review'])
                #print(f"ANALYSING REVIEW FROM SENTIMENT SERVICE {response}")
                review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status":200,"reviews":reviews})
    return JsonResponse({"status":400,"message":"Bad Request"})

def get_dealer_details(request, dealer_id):
    '''# Create a `get_dealer_details` view to render the dealer details'''
    if dealer_id is not None:
        endpoint = "/fetchDealer/"+str(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status":200,"dealer":dealership})
    return JsonResponse({"status":400,"message":"Bad Request"})

def add_review(request):
    '''# Create a `add_review` view to submit a review'''
    if request.user.is_anonymous is False:
        data = json.loads(request.body)
        try:
            response = post_review(data)
            print(response)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    return JsonResponse({"status":403,"message":"Unauthorized"})
