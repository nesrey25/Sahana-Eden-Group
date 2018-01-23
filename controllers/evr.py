# -*- coding: utf-8 -*-
#registers individuals or families into the Sahana Eden project. Allows for the update of individuals that come through 
#the Sahana Eden project or through a specific location that an individual (or a group) comes through 
#prompts for data entry of a person EX: resident of __________
    #Different functions that are called throughout the code 
        #self updates and outputs the information of an individual using 'field' and 'label' 
        #levels: Set the root logger level to the specified level
        #method: a function that takes a class instance as its first parameter. Methods are members of classes
        #
"""
    Evacuees Registry
"""
#allows the string module to hold everything in controller 
#allows resourcename to hold everything that functions holds 
module = request.controller
resourcename = request.function

#HTTP: PUT, DELETE, HEAD and OPTIONS 
#if statement that if an error occurs, the user is directed to the error 404 page
#if information goes through and has access, then the user is allowed to add new sahana eden members or groups to the program 
if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)
#Response Content 
s3db.set_method("pr", "group",
                method = "add_members",
                action = s3db.evr_AddGroupMembers)

# -----------------------------------------------------------------------------
#retruns the module home page 
def index():
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
#homepage for non-admin users
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Cases
    s3_redirect_default(URL(f="person"))

# -----------------------------------------------------------------------------
#person function that allows for the input of a new person into the Sahana Eden registry
#"Creates a new contact" in the system like process that allows Sahana Eden to keep track of who has used a registered location or car
def person():
    """
        REST controller to register evacuees
    """

    # @todo: this will not allow pre-existing person records
    #        to be added as EVR cases - need a filter+action
    #        solution instead
    s3.filter = s3base.S3FieldSelector("case.id") != None

    # Custom Method for Contacts
    s3db.set_method("pr", "person",
                    method = "contacts",
                    action = s3db.pr_Contacts)

    def prep(r):

        fiscal_code = s3db.evr_case.fiscal_code
        levels = current.gis.get_relevant_hierarchy_levels()

        if r.method == "update":
            fiscal_code.requires = None
        else:
            fiscal_code.requires = \
                    IS_EMPTY_OR(IS_NOT_IN_DB(db(db.evr_case.deleted != True),
                                             fiscal_code),
                                null=""
                                )
        #report data of an individual that is logged into the file system when checked into a Sahana Eden site
        report_fields = ["id",
                         "last_name",
                         "case.organisation_id",
                         "gender",
                         "date_of_birth",
                         "person_details.nationality",
                         "person_details.marital_status",
                         "shelter_registration.shelter_id",
                         "shelter_registration.check_in_date",
                         "shelter_registration.check_out_date",
                         ]
        #registres a specific unit to that individual 
        if settings.get_cr_shelter_housing_unit_management():
            report_fields.append("shelter_registration.shelter_unit_id")
        #levels update, add elements to the list 
        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)

        report_options = Storage(
                                 rows=report_fields,
                                 cols=report_fields,
                                 fact=report_fields,
                                 defaults=Storage(
                                                  rows="shelter_registration.shelter_id",
                                                  cols="gender",
                                                  #totals=True,
                                                  )
                                 )
        list_fields = ["id",
                       "first_name",
                       #"middle_name",
                       "last_name",
                       "gender",
                       "date_of_birth",
                       ]
        #sets link to the organization/shelter/housing that the individual is staying at in the system 
        if settings.get_evr_link_to_organisation():
            list_fields.append("case.organisation_id")
        list_fields.append("shelter_registration.shelter_id")
        if settings.get_cr_shelter_housing_unit_management():
            list_fields.append("shelter_registration.shelter_unit_id")
        list_fields.append("shelter_registration.check_in_date")
        list_fields.append("shelter_registration.check_out_date")

        r.resource.configure(list_fields = list_fields,
                             report_options = report_options)

        if r.interactive:
            if not r.component:

                resource = r.resource

                # Filter widgets
                from s3 import S3OptionsFilter, S3TextFilter, S3LocationFilter, S3DateFilter
                filter_widgets = [
                    S3TextFilter(["first_name",
                                #"middle_name",
                                "last_name",
                                #"local_name",
                                "identity.value",
                                "case.fiscal_code",
                                ],
                                label = T("Name and/or ID"),
                                comment = T("To search for a person, enter any of the "
                                            "first, middle or last names and/or an ID "
                                            "number of a person, separated by spaces. "
                                            "You may use % as wildcard."),
                                ),
                 #Sets a specific piece of data to a string name that can be accessed later on as a label(displays text of an image to the user)
                    S3LocationFilter("address.location_id",
                                    label = T("Current Residence"),
                                    levels = levels,
                                    ),
                    S3DateFilter("date_of_birth",
                                label = T("Date Of Birth")
                                ),
                    S3OptionsFilter("person_details.nationality",
                                    label = T("Nationality"),
                                    ),
                    S3OptionsFilter("case.organisation_id",
                                    label = T("Organisation"),
                                    ),
                    S3OptionsFilter("shelter_registration.shelter_id",
                                    label = T("Shelter"),
                                    ),
                    S3OptionsFilter("shelter_registration.registration_status",
                                    label = T("Registration Status"),
                                    ),
                ]

                # Creates a custom form for individuals or for a group that is checking in 
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm("case.organisation_id",
                                            "first_name",
                                            "middle_name",
                                            "last_name",
                                            "date_of_birth",
                                            "location_id",
                                            "person_details.place_of_birth",
                                            "case.fiscal_code",
                                            S3SQLInlineComponent(
                                                "identity",
                                                label = T("Identity Documents"),
                                                fields = ["type",
                                                        "value",
                                                        ],
                                            ),
                                            "person_details.nationality",
                                            "gender",
                                            "person_details.marital_status",
                                            "person_details.religion",
                                            "person_details.occupation",
                                            #"person_details.company",
                                            "comments",
                                            )
                resource.configure(crud_form = crud_form,
                                   filter_widgets = filter_widgets,
                                   )

            elif r.component_name == "shelter_registration":

                if settings.get_cr_shelter_housing_unit_management():
                    # Dynamically update options for shelter_unit_id
                    # when a shelter_id gets selected
                    # Access direct request from s3 and import it to SEPARATORS
                    from s3 import SEPARATORS
                    options = {"trigger": "shelter_id",
                               "target": "shelter_unit_id",
                               "lookupPrefix": "cr",
                               "lookupResource": "shelter_unit",
                               }
                    s3.jquery_ready.append('''$.filterOptionsS3(%s)''' % \
                                           json.dumps(options,
                                                      separators=SEPARATORS))
        #sets the field data in a pdf or an excel like spreadsheet 
        elif r.representation in ("pdf", "xls"):
            # List fields
            list_fields = ["id",
                           "first_name",
                           #"middle_name",
                           "last_name",
                           "gender",
                           #"date_of_birth",
                           (T("Age"), "age"),
                           "person_details.nationality",
                           "person_details.religion",
                           (T("Contact"), "contact.value"),
                           (T("Shelter"), "shelter_registration.shelter_id$name")
                           ]
            r.resource.configure(list_fields=list_fields)
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person",
                              rheader = s3db.evr_rheader)

# -----------------------------------------------------------------------------
def group():
    """
        REST controller to register families and other groups
    """

    evr_group_types = settings.get_evr_group_types()

    # Pre-process
    def prep(r):
        resource = r.resource
        if not r.component:
            FS = s3base.S3FieldSelector
            query = (FS("system") == False) & \
                    (FS("group_type").belongs(evr_group_types.keys()))
            resource.add_filter(query)

            # Fields to be displayed in the group table
            resource.configure(# Redirect to member list when a new group
                               # has been created
                               create_next = URL(f="group",
                                                 args=["[id]",
                                                       "group_membership"],
                                                 ),
                               list_fields = ["id",
                                              "name",
                                              "description",
                                              "group_type",
                                              "group_membership.person_id",
                                              (T("Contact"), "contact.value")
                                              ],
                               )
        #If there is a group checking into the Sahana Eden Project 
            if r.interactive:
                # Override the options for group_type,
                # only show evr_group_types
                resource.table.group_type.requires = IS_IN_SET(evr_group_types,
                                                               zero=None)

        component = r.component
        if component and component.name == "group_membership":
            component.configure(list_fields = ["id",
                                               "group_id$name",
                                               "group_id$description",
                                               "group_id$group_type",
                                               "person_id",
                                               "person_id$date_of_birth",
                                               "group_head"
                                               ],
                                # No embedded add-form
                                listadd = False,
                                )
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            component = r.component
            if not component:
                update_url = URL(args=["[id]", "group_membership"])
            elif component.name == "group_membership" and not r.method:
                # Allows the user to enter a new member or members to the Sahana Eden system 
                # Custom add-button that redirects to the add_members
                # action (opens on a separate tab)
                buttons = output.get("buttons", {})
                buttons["add_btn"] = A(T("Add Members"),
                                       _href = r.url(component = "",
                                                     method = "add_members",
                                                     ),
                                       _class = "action-btn add",
                                       )
                output["buttons"] = buttons
        return output
    s3.postp = postp

    output = s3_rest_controller("pr", "group",
                                rheader = s3db.evr_rheader)

    return output

# END =========================================================================
