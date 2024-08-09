from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.


# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to authenticate user
    user = authenticate(username=username, password=password)
    response_data = {"userName": username}
    if user is not None:
        # If user is valid, log in the user
        login(request, user)
        response_data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(response_data)


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return JsonResponse({"userName": ""})


# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
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
    except User.DoesNotExist:
        logger.debug(f"{username} is a new user")

    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        # Login the user
        login(request, user)
        response_data = {"userName": username, "status": "Authenticated"}
    else:
        response_data = {"userName": username, "error": "Already Registered"}

    return JsonResponse(response_data)


# Update the `get_dealerships` to render list of dealerships
def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = f"/fetchDealers/{state}"

    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        reviews = get_request(endpoint)
        for review_detail in reviews:
            sentiment_response = analyze_review_sentiments(
                review_detail['review'])
            review_detail['sentiment'] = sentiment_response['sentiment']
        return JsonResponse({"status": 200, "reviews": reviews})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = f"/fetchDealer/{dealer_id}"
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    return JsonResponse({"status": 400, "message": "Bad Request"})


# Create an `add_review` view to submit a review
def add_review(request):
    if not request.user.is_anonymous:
        data = json.loads(request.body)
        try:
            post_review(data)
            return JsonResponse({"status": 200})
        except Exception:
            return JsonResponse({
                "status": 401,
                "message": "Error in posting review"
            })
        finally:
            print("add_review request successful!")
    return JsonResponse({
        "status": 403,
        "message": "Unauthorized"
    })


# Method to get cars
def get_cars(request):
    count = CarMake.objects.count()
    if count == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = [
        {"CarModel": car_model.name, "CarMake": car_model.car_make.name}
        for car_model in car_models
    ]
    return JsonResponse({"CarModels": cars})
