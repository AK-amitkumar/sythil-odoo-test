# -*- coding: utf-8 -*
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint
import random
import time

class ResDating(models.Model):

    _name = "res.dating"
    
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string="State")
    num_profiles = fields.Integer(string="Num Profiles", default="1000")
    min_age = fields.Integer(string="Min Age", default="18")
    max_age = fields.Integer(string="Max Age", default="60")

    @api.one
    def delete_fake_profiles(self):
        for fake in self.env['res.partner'].search([('fake_profile','=',True)]):
            fake.unlink()
    
    @api.one
    def create_fake_profiles(self):
        calc_min_days = 365 * self.min_age
        calc_max_days = 365 * self.max_age
                
        my_delta_young_time = datetime.utcnow() - timedelta(days=calc_min_days)
        my_delta_old_time = datetime.utcnow() - timedelta(days=calc_max_days)	        

        suburb_list = self.env['res.better.zip'].search([('country_id','=',self.country_id.id),('state_id','=',self.state_id.id)])

        male_gender_id = self.env['res.partner.gender'].search([('name','=','Male')])[0].id
        female_gender_id = self.env['res.partner.gender'].search([('name','=','Female')])[0].id
        
        for i in range(0, self.num_profiles):
	    #random name and with it gender
            first_name = self.env['res.dating.fake.first'].browse(randint(1, 4999))
            last_name = self.env['res.dating.fake.last'].browse(randint(1, 4999))
            
            gender = self.env['res.partner.gender'].search([('name','=',first_name.gender)])[0].id

            #random age
	    birth_date = my_delta_old_time + timedelta(seconds=randint(0, int((my_delta_young_time - my_delta_old_time).total_seconds())))
            age = relativedelta(date.today(), birth_date).years

            #random age pref
            min_age_pref = randint(self.min_age, self.max_age)
            max_age_pref = randint(min_age_pref, self.max_age)

            #random relationship type
            relationship_type = self.env['res.partner.relationship'].browse(randint(1, self.env['res.partner.relationship'].search_count([]) ) )
            
            #random suburb
            rand_suburb = suburb_list[randint(0, len(suburb_list) - 1)]
                
            #random profile visibilty
            rand_profile_vis = randint(1, 100)
            profile_vis = ""
            if rand_profile_vis <= 80:
                #80% of being members only
                profile_vis = "members_only"
            elif rand_profile_vis <= 100:
                #20% of being public
                profile_vis = "public"
                
            #random profile text
            profile_text = "I am " + str(age) + " year old " + first_name.gender + " seeking " + str(relationship_type.name)
            
            #create the partner
            new_partner = self.env['res.partner'].create({'profile_text': profile_text,'profile_visibility': profile_vis,'dating':'True', 'fake_profile':'True', 'birth_date': birth_date, 'firstname':first_name.name, 'lastname':last_name.name,'gender':gender, 'zip_id':rand_suburb.id, 'country_id':rand_suburb.country_id.id, 'state_id':rand_suburb.state_id.id, 'city':rand_suburb.city,'zip':rand_suburb.name, 'age':age, 'relationship_type': relationship_type.id, 'min_age_pref':min_age_pref,'max_age_pref':max_age_pref})           
            
            #random gender pref
            rand_gender_pref = randint(1, 100)
            if rand_gender_pref <= 80:
                #80% chance of being straight
                if first_name.gender == "Male":
                    new_partner.gender_pref = [(4, female_gender_id)]
                elif first_name.gender == "Female":
                    new_partner.gender_pref = [(4, male_gender_id)]
            elif rand_gender_pref <= 90:
                #10% chance of being gay
                if first_name.gender == "Male":
                    new_partner.gender_pref = [(4, male_gender_id)]
                elif first_name.gender == "Female":
                    new_partner.gender_pref = [(4, female_gender_id)]    
            elif rand_gender_pref <= 100:
                #10% chance of being bi
                new_partner.gender_pref = [(4, male_gender_id)]
                new_partner.gender_pref = [(4, female_gender_id)]
                    
                        
class ResDatingMessage(models.Model):

    _name = "res.dating.message"
    
    partner_id = fields.Many2one('res.partner', string='From Partner')
    to_id = fields.Many2one('res.partner', string='To Partner')
    message = fields.Text(string="Message")
    type =  fields.Selection([('regular','Regular'), ('like','Like')], default="regular", string="Type")
