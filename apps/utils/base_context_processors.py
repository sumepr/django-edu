from operation.models import UserFavorite

def base_context(request):
	user_fav = UserFavorite.objects.filter(user = request.user.id, fav_type=1).count()


	context = {
		'base_user_fav_lenth':user_fav,
	}
	return context