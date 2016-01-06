import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)
import werkzeug
from datetime import datetime
import json
import math

class WebsiteDatingController(http.Controller):

    @http.route('/dating/profiles/like', type="http", auth="user", website=True)
    def dating_like(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	 
	member_id = int(values['member_id'])	
	
	like_list = http.request.env.user.partner_id.like_list
        
        #check if the partner has already liked this member
        already_liked = False
        
        if http.request.env['res.partner'].browse(member_id) in like_list:
            already_liked = True
         
        
        if already_liked == False:
            #add to like list
            http.request.env.user.partner_id.like_list = [(4, member_id)]
            
            #message the member
            message = http.request.env.user.partner_id.firstname + " likes you.\n\nClick <a href=\"/dating/profiles/" + str(http.request.env.user.partner_id.id) + "\"/>here</a> to view this members profile."
            http.request.env["res.dating.message"].sudo().create({'partner_id': http.request.env.user.partner_id.id, 'to_id': member_id, 'type': 'like', 'message':message})
    
        return werkzeug.utils.redirect("/dating/profiles/" + str(member_id) )

    @http.route('/dating/profile/update', type="http", auth="user", website=True)
    def dating_profile_update(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	 
	
	member_id = int(values['member_id'])
	
	#Only the owner can update there profile
	if http.request.env.user.partner_id.id != member_id:
            return "Permission Denied"
	
	member = http.request.env['res.partner'].search([('id','=',member_id), ('dating','=',True)])[0]
        
        member.profile_visibility = values['profile_visibility']
        
        return werkzeug.utils.redirect("/dating/profiles/" + str(member_id) )
    
    @http.route('/dating/profiles', type="http", auth="public", website=True)
    def dating_list(self, **kwargs):
    
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value 
 
        search_list = []
        return_dict = {}
        
        
        #only dating members
        search_list.append(('dating','=','True'))
        
        if http.request.env.user.partner_id.name == 'Public user':
            #if not logged in only show public profiles
	    search_list.append(('profile_visibility','=','public'))                
        else:
            #if logged in they can view all non private profiles
            search_list.append(('profile_visibility','!=','not_listed'))        

        
        
        #min age preference
        if 'min_age' in values and values['min_age'] != '':
            search_list.append(('age','>=',values['min_age']))
        
        #max age preference
        if 'max_age' in values and values['max_age'] != '':
            search_list.append(('age','<=',values['max_age']))

        #gender preference
        if 'gender' in values and values['gender'] != '':
            search_list.append(('gender','=',values['gender']))
                     
        if 'dist' in values and values['dist'] != '':
            
            user_suburb = http.request.env.user.partner_id.zip_id
            
	    mylon = float(user_suburb.longitude)
	    mylat = float(user_suburb.latitude)
	    dist = float(values['dist']) * 0.621371
	    lon_min = mylon-dist/abs(math.cos(math.radians(mylat))*69);
	    lon_max = mylon+dist/abs(math.cos(math.radians(mylat))*69);
	    lat_min = mylat-(dist/69);
	    lat_max = mylat+(dist/69);
	            
	    close_suburbs = http.request.env['res.better.zip'].search([('longitude','>=',lon_min), ('longitude','<=',lon_max), ('latitude','<=',lat_min), ('latitude','>=',lat_max)])
  
            search_list.append(('zip_id.longitude','>=',lon_min))
            search_list.append(('zip_id.longitude','<=',lon_max))
            search_list.append( ('zip_id.latitude','<=',lat_min) )
            search_list.append( ('zip_id.latitude','>=',lat_max) )
            
            
        my_dates = http.request.env['res.partner'].sudo().search(search_list, limit=15)
        my_dates_count = len(my_dates)
        
        return http.request.render('website_dating.my_dating_list', {'my_dates': my_dates, 'my_dates_count': my_dates_count} )

    @http.route('/dating/profiles/settings', type="http", auth="user", website=True)
    def dating_profile_settings(self, **kwargs):
        
        #only logged in members can view this page
        if http.request.env.user.partner_id.name != 'Public user':
            return http.request.render('website_dating.my_dating_profile_settings', {'my_date': http.request.env.user.partner_id} )
        else:
            return "Permission Denied"
            
    @http.route('/dating/profiles/<member_id>', type="http", auth="public", website=True)
    def dating_profile(self, member_id, **kwargs):
        
        you_like = False
        they_like = False
        can_view = False
        
        member = http.request.env['res.partner'].sudo().search([('id','=',member_id), ('dating','=',True)])[0]
        partner = http.request.env.user.partner_id
        
        
        for you_likes in partner.like_list:
            if int(member_id) == int(you_likes.id):
                you_like = True
                break
            
        for they_likes in member.like_list:
            if partner.id == they_likes.id:
                they_like = True
                break
        
        
        if member.profile_visibility == "public":
            #everyone can view public profiles
            can_view = True
        elif member.profile_visibility == "members_only":
            #only logged in can view this profile
            if http.request.env.user.partner_id.name != 'Public user':
                can_view = True
        elif member.profile_visibility == "not_listed":
            #if this member likes you, you can view this profile
            if they_like == True:
                can_view = True
        
        #the owner can view there own profile
        if http.request.env.user.partner_id.id == int(member_id):
            can_view = True
        
        if can_view:
            return http.request.render('website_dating.my_dating_profile', {'my_date': member, 'you_like':you_like, 'they_like':they_like} )
        else:
            return "Permission Denied"